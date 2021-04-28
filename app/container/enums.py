DELETE_SUCCESS = (0, '删除容器成功。')
DELETE_FAILED = (3001, '删除容器失败。')
CREATE_SUCCESS = (0, '创建容器成功。')
CREATE_FAILED = (3002, '创建容器失败。')

START_SUCCESS = (0, '启动容器成功。')
START_FAILED = (3003, '启动容器失败。')
STOP_SUCCESS = (0, '停止容器成功。')
STOP_FAILED = (3003, '停止容器失败。')
RESTART_SUCCESS = (0, '重启容器成功。')
RESTART_FAILED = (3004, '重启容器失败。')

RENAME_SUCCESS = (0, '容器更名成功。')
RENAME_FAILED = (3005, '容器更名失败。')

COMMIT_SUCCESS = (0, '提交容器镜像成功。')
COMMIT_FAILED = (3006, '提交容器镜像失败。')

RUN_SUCCESS = (0, '创建（运行）容器成功。')
RUN_FAILED = (3007, '创建（运行）容器失败。')

TERMINAL_FAILED = (3008, '打开容器终端失败，该容器未启用"虚拟终端"及"交互模式"。')
TERMINAL_FAILED_NOT_EXISTED = (3009, '打开终端失败，容器不存在。')

TERMINAL_PERMISSION_DENIED = dict(msg='无权限访问。')
TERMINAL_SESSION_INVALID = dict(msg='会话无效，请重新打开终端。')
TERMINAL_CONTAINER_NOT_EXISTED = dict(msg='容器不存在。')
