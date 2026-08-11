import asyncio
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import StackContext, get_stack_ctx
from app.core import stack_registry
from app.core.database import async_session
from app.core.security import get_current_token
from app.schemas.common import StatusResponse
from app.schemas.stack import (
    DestroyRequest,
    DownRequest,
    FileContent,
    FileSaveResult,
    GitCancelRequest,
    GitCloneRequest,
    GitCloneResult,
    GitCreateRequest,
    StackCreate,
    StackImport,
    StackFile,
    StackItem,
    StackMeta,
    StackTaskItem,
    TaskCreated,
)
from app.services import git as git_service
from app.services.cli import CliError, CliTask
from app.services.compose import stack_tasks

router = APIRouter(
    prefix="/stacks",
    tags=["stacks"],
    dependencies=[Depends(get_current_token)],
)


def _require_compose(ctx: StackContext):
    if not ctx.compose:
        raise HTTPException(status_code=503, detail="compose CLI not available")
    return ctx.compose


def _task_item(t: CliTask) -> StackTaskItem:
    return StackTaskItem(
        id=t.id, kind=t.kind, stack=t.stack, status=t.status,
        returncode=t.returncode, error=t.error,
        started_at=t.started_at, finished_at=t.finished_at,
    )


async def _get_item(ctx: StackContext, name: str) -> dict:
    registrations = await stack_registry.list_all(ctx.session)
    item = await ctx.stack.get(name, registrations)
    if not item:
        raise HTTPException(status_code=404, detail="Stack not found")
    return item


def _item_cwd(item: dict) -> str:
    return item["working_dir"] or str(Path(item["config_files"][0]).parent)


async def _launch(ctx: StackContext, kind: str, name: str, launch) -> TaskCreated:
    compose = _require_compose(ctx)
    task = await stack_tasks.start(compose.executor, kind, name, launch)
    if task is None:
        raise HTTPException(status_code=409, detail="Operation already in progress")
    return TaskCreated(task_id=task.id)


@router.get("/meta", response_model=StackMeta)
async def get_meta(ctx: StackContext = Depends(get_stack_ctx)):
    cli = ctx.compose.cli if ctx.compose else None
    return StackMeta(
        cli_available=cli is not None,
        cli_version=cli.version if cli else None,
        cli_major=cli.major if cli else None,
        cli_binary=cli.binary if cli else None,
        progress=cli.progress if cli else False,
        container_mode=ctx.stack.container_mode,
        stacks_dir=ctx.stack.stacks_dir,
        git_available=git_service.git_available(),
    )


@router.get("/tasks", response_model=List[StackTaskItem])
async def list_tasks(ctx: StackContext = Depends(get_stack_ctx)):
    compose = _require_compose(ctx)
    return [_task_item(t) for t in compose.executor.recent_tasks()]


@router.post("/tasks/{task_id}/cancel", response_model=StatusResponse)
async def cancel_task(task_id: str, ctx: StackContext = Depends(get_stack_ctx)):
    compose = _require_compose(ctx)
    await compose.executor.cancel(task_id)
    return StatusResponse()


@router.get("", response_model=List[StackItem])
async def list_stacks(ctx: StackContext = Depends(get_stack_ctx)):
    registrations = await stack_registry.list_all(ctx.session)
    return await ctx.stack.list(registrations)


@router.post("", response_model=TaskCreated, status_code=201)
async def create_stack(body: StackCreate, ctx: StackContext = Depends(get_stack_ctx)):
    compose = _require_compose(ctx)
    registrations = await stack_registry.list_all(ctx.session)
    if await ctx.stack.get(body.name, registrations):
        raise HTTPException(status_code=409, detail="Stack name already exists")
    try:
        stack_dir, compose_file = ctx.stack.resolve_create_target(
            body.name, body.directory,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if stack_dir.exists() and any(stack_dir.iterdir()):
        raise HTTPException(status_code=409, detail=f"Directory not empty: {stack_dir}")

    stack_dir.mkdir(parents=True, exist_ok=True)
    compose_file.write_text(body.content)
    if body.env and body.env.strip():
        (stack_dir / ".env").write_text(body.env)
    try:
        await compose.validate([str(compose_file)], cwd=str(stack_dir))
    except CliError as e:
        compose_file.unlink(missing_ok=True)
        shutil.rmtree(stack_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Invalid compose file:\n{e.output}")

    await stack_registry.register(
        ctx.session, body.name, str(stack_dir), str(compose_file), "created",
    )
    return await _launch(ctx, "up", body.name, lambda on_data, on_done: compose.up(
        body.name, [str(compose_file)], str(stack_dir), on_data, on_done=on_done,
    ))


async def _git_stack_dir(ctx: StackContext, name: str, directory: Optional[str]) -> Path:
    registrations = await stack_registry.list_all(ctx.session)
    if await ctx.stack.get(name, registrations):
        raise HTTPException(status_code=409, detail="Stack name already exists")
    try:
        stack_dir, _ = ctx.stack.resolve_create_target(name, directory)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return stack_dir


@router.post("/git/clone", response_model=TaskCreated)
async def git_clone_stack(
    body: GitCloneRequest, ctx: StackContext = Depends(get_stack_ctx),
):
    compose = _require_compose(ctx)
    stack_dir = await _git_stack_dir(ctx, body.name, body.directory)
    if stack_dir.exists() and any(stack_dir.iterdir()):
        raise HTTPException(status_code=409, detail=f"Directory not empty: {stack_dir}")
    if not git_service.git_available():
        raise HTTPException(status_code=503, detail="git CLI not available")

    async def _cleanup(task: CliTask, broadcast_done) -> None:
        await broadcast_done(task)
        if task.status != "done":
            await asyncio.to_thread(shutil.rmtree, stack_dir, ignore_errors=True)

    return await _launch(ctx, "clone", body.name, lambda on_data, on_done: (
        git_service.clone_stream(
            compose.executor, body.repo_url, body.branch, stack_dir, on_data,
            on_done=lambda task: _cleanup(task, on_done),
        )
    ))


def _cloned_repo_dir(ctx: StackContext, name: str, directory: Optional[str]) -> Path:
    try:
        stack_dir, _ = ctx.stack.resolve_create_target(name, directory)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not (stack_dir / ".git").is_dir():
        raise HTTPException(status_code=400, detail="Repository not cloned yet")
    return stack_dir


@router.get("/git/candidates", response_model=GitCloneResult)
async def git_clone_candidates(
    name: str,
    directory: Optional[str] = None,
    ctx: StackContext = Depends(get_stack_ctx),
):
    registrations = await stack_registry.list_all(ctx.session)
    if await ctx.stack.get(name, registrations):
        raise HTTPException(status_code=409, detail="Stack name already exists")
    stack_dir = _cloned_repo_dir(ctx, name, directory)
    compose_files, env_templates = git_service.scan_candidates(stack_dir)
    if not compose_files:
        shutil.rmtree(stack_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="No compose file found in repository")
    return GitCloneResult(
        name=name, compose_files=compose_files, env_templates=env_templates,
    )


@router.get("/git/file", response_model=StackFile)
async def git_read_file(
    name: str,
    path: str,
    directory: Optional[str] = None,
    ctx: StackContext = Depends(get_stack_ctx),
):
    stack_dir = _cloned_repo_dir(ctx, name, directory)
    try:
        file_path = git_service.resolve_in_repo(stack_dir, path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    return await _read_stack_file(file_path)


@router.post("/git/create", response_model=TaskCreated, status_code=201)
async def git_create_stack(
    body: GitCreateRequest, ctx: StackContext = Depends(get_stack_ctx),
):
    compose = _require_compose(ctx)
    stack_dir = await _git_stack_dir(ctx, body.name, body.directory)
    if not (stack_dir / ".git").is_dir():
        raise HTTPException(status_code=400, detail="Repository not cloned yet")
    try:
        compose_file = git_service.resolve_in_repo(stack_dir, body.compose_path)
        template = (
            git_service.resolve_in_repo(stack_dir, body.env_template_path)
            if body.env_template_path else None
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not compose_file.is_file():
        raise HTTPException(
            status_code=400, detail=f"Compose file not found: {body.compose_path}",
        )
    if template is not None and not template.is_file():
        raise HTTPException(
            status_code=400,
            detail=f"Env template not found: {body.env_template_path}",
        )
    if body.content is not None:
        await asyncio.to_thread(compose_file.write_text, body.content)
    env_target = compose_file.parent / ".env"
    if body.env is not None:
        if body.env.strip():
            await asyncio.to_thread(env_target.write_text, body.env)
    elif template is not None and not env_target.exists():
        await asyncio.to_thread(shutil.copy2, template, env_target)
    try:
        await compose.validate([str(compose_file)], cwd=str(compose_file.parent))
    except CliError as e:
        raise HTTPException(status_code=400, detail=f"Invalid compose file:\n{e.output}")

    await stack_registry.register(
        ctx.session, body.name, str(stack_dir), str(compose_file), "git",
    )
    return await _launch(ctx, "up", body.name, lambda on_data, on_done: compose.up(
        body.name, [str(compose_file)], str(compose_file.parent),
        on_data, on_done=on_done,
    ))


@router.post("/git/cancel", response_model=StatusResponse)
async def git_cancel_stack(
    body: GitCancelRequest, ctx: StackContext = Depends(get_stack_ctx),
):
    """Remove a cloned repo when the user abandons the git create flow."""
    if await stack_registry.get(ctx.session, body.name):
        raise HTTPException(status_code=409, detail="Stack already registered")
    try:
        stack_dir, _ = ctx.stack.resolve_create_target(body.name, body.directory)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if (stack_dir / ".git").is_dir():
        await asyncio.to_thread(shutil.rmtree, stack_dir, ignore_errors=True)
    return StatusResponse()


@router.post("/import", response_model=StatusResponse)
async def import_stack(body: StackImport, ctx: StackContext = Depends(get_stack_ctx)):
    registrations = await stack_registry.list_all(ctx.session)
    if await stack_registry.get(ctx.session, body.name):
        raise HTTPException(status_code=409, detail="Stack already registered")
    item = await ctx.stack.get(body.name, registrations)
    if not item:
        raise HTTPException(status_code=404, detail="Stack not discovered")
    if not item["config_files"]:
        raise HTTPException(status_code=400, detail="Stack has no compose file path")
    if ctx.stack.container_mode and not ctx.stack.file_accessible(
        item["config_files"], registered=False,
    ):
        raise HTTPException(
            status_code=400,
            detail="Stack files are outside stacks_dir and unreachable in this deployment",
        )
    await stack_registry.register(
        ctx.session, body.name, item["working_dir"],
        ",".join(item["config_files"]), "imported",
    )
    return StatusResponse()


@router.get("/{name}", response_model=StackItem)
async def get_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    return await _get_item(ctx, name)


@router.delete("/{name}/registration", response_model=StatusResponse)
async def unregister_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    if not await stack_registry.unregister(ctx.session, name):
        raise HTTPException(status_code=404, detail="Registration not found")
    return StatusResponse()


@router.post("/{name}/start", response_model=StatusResponse)
async def start_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    return await _lifecycle(ctx, name, "start")


@router.post("/{name}/stop", response_model=StatusResponse)
async def stop_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    return await _lifecycle(ctx, name, "stop")


@router.post("/{name}/restart", response_model=StatusResponse)
async def restart_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    return await _lifecycle(ctx, name, "restart")


async def _lifecycle(ctx: StackContext, name: str, action: str) -> StatusResponse:
    compose = _require_compose(ctx)
    lock = await stack_tasks.stack_lock(name)
    if lock.locked():
        raise HTTPException(status_code=409, detail="Operation already in progress")
    async with lock:
        try:
            await compose.lifecycle(name, action)
        except CliError as e:
            raise HTTPException(status_code=400, detail=e.output.strip() or str(e))
    return StatusResponse()


@router.post("/{name}/down", response_model=TaskCreated)
async def down_stack(
    name: str, body: DownRequest, ctx: StackContext = Depends(get_stack_ctx),
):
    compose = _require_compose(ctx)
    await _get_item(ctx, name)
    return await _launch(ctx, "down", name, lambda on_data, on_done: compose.down(
        name, body.remove_volumes, on_data, on_done=on_done,
    ))


@router.post("/{name}/destroy", response_model=TaskCreated)
async def destroy_stack(
    name: str,
    body: DestroyRequest,
    ctx: StackContext = Depends(get_stack_ctx),
):
    compose = _require_compose(ctx)
    item = await _get_item(ctx, name)
    if not item["registered"]:
        raise HTTPException(
            status_code=400,
            detail="Only registered stacks can be destroyed",
        )
    _guard_files(ctx, item)

    async def _cleanup(task: CliTask, broadcast_done) -> None:
        await broadcast_done(task)
        # Only tear down registration/files when compose down succeeded;
        # a failed down leaves running containers that must stay manageable.
        if task.status != "done":
            return
        async with async_session() as session:
            await stack_registry.unregister(session, name)
        if body.delete_files and item["source"] in ("created", "git"):
            path = Path(item["working_dir"])
            if path.exists():
                await asyncio.to_thread(shutil.rmtree, path, ignore_errors=True)

    return await _launch(ctx, "destroy", name, lambda on_data, on_done: compose.down(
        name, body.remove_volumes, on_data,
        on_done=lambda task: _cleanup(task, on_done),
    ))


@router.post("/{name}/pull", response_model=TaskCreated)
async def pull_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    compose = _require_compose(ctx)
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    cwd = _item_cwd(item)
    return await _launch(ctx, "pull", name, lambda on_data, on_done: compose.pull(
        name, item["config_files"], cwd, on_data, on_done=on_done,
    ))


@router.post("/{name}/up", response_model=TaskCreated)
async def up_stack(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    compose = _require_compose(ctx)
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    cwd = _item_cwd(item)
    return await _launch(ctx, "up", name, lambda on_data, on_done: compose.up(
        name, item["config_files"], cwd, on_data, on_done=on_done,
    ))


def _guard_files(ctx: StackContext, item: dict) -> None:
    try:
        ctx.stack.check_file_allowed(item["config_files"], item["registered"])
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


def _env_path(item: dict) -> Path:
    return Path(item["config_files"][0]).parent / ".env"


async def _read_stack_file(path: Path, allow_missing: bool = False) -> StackFile:
    try:
        content = await asyncio.to_thread(path.read_text)
    except FileNotFoundError:
        if not allow_missing:
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        content = ""
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StackFile(path=str(path), content=content)


async def _write_stack_file(
    ctx: StackContext, item: dict, path: Path, content: str,
) -> FileSaveResult:
    try:
        if path.exists():
            backup = Path(str(path) + ".bak")
            await asyncio.to_thread(backup.write_text, path.read_text())
        await asyncio.to_thread(path.write_text, content)
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if ctx.compose:
        try:
            await ctx.compose.validate(item["config_files"], cwd=str(path.parent))
        except CliError as e:
            return FileSaveResult(valid=False, error=e.output.strip())
    return FileSaveResult(valid=True)


@router.get("/{name}/file", response_model=StackFile)
async def read_stack_file(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    return await _read_stack_file(Path(item["config_files"][0]))


@router.put("/{name}/file", response_model=FileSaveResult)
async def write_stack_file(
    name: str, body: FileContent, ctx: StackContext = Depends(get_stack_ctx),
):
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    return await _write_stack_file(
        ctx, item, Path(item["config_files"][0]), body.content,
    )


@router.get("/{name}/env", response_model=StackFile)
async def read_stack_env(name: str, ctx: StackContext = Depends(get_stack_ctx)):
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    return await _read_stack_file(_env_path(item), allow_missing=True)


@router.put("/{name}/env", response_model=FileSaveResult)
async def write_stack_env(
    name: str, body: FileContent, ctx: StackContext = Depends(get_stack_ctx),
):
    item = await _get_item(ctx, name)
    _guard_files(ctx, item)
    return await _write_stack_file(ctx, item, _env_path(item), body.content)
