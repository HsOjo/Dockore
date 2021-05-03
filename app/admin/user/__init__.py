from saika.decorator import *

from .enums import *
from .forms import *
from .service import AdminUserService
from ..admin_api import AdminAPIController


@controller('/api/admin/user')
class AdminUser(AdminAPIController):
    @get
    @rule('/list')
    @form(ListForm)
    def list(self):
        pagi = AdminUserService.list(**self.form.data)
        self.success(page=pagi.page, pages=pagi.pages, items=[dict(
            id=item.id,
            username=item.username,
            role_type=item.role.type,
        ) for item in pagi.items], total=pagi.total)

    @get
    @rule('/item/<int:id>')
    def item(self, id: int):
        item = AdminUserService.item(id)
        if item is None:
            self.error(*USER_NOT_EXISTED)

        self.success(item=dict(
            id=item.id,
            username=item.username,
            role_type=item.role.type,
        ))

    @post
    @form(AddForm)
    @rule('/add')
    def add(self):
        AdminUserService.add(**self.form.data)
        self.success(*ADD_SUCCESS)

    @post
    @form(EditForm)
    @rule('/edit')
    def edit(self):
        if self.form.id.data == self.current_user.id:
            if self.form.role_type.data != RoleShip.TYPE_ADMIN:
                if AdminUserService.count_admin() <= 1:
                    self.error(*SAVE_ONE_ADMIN)

        if AdminUserService.edit(**self.form.data) is False:
            self.error(*USER_NOT_EXISTED)
        self.success(*EDIT_SUCCESS)

    @post
    @rule('/delete')
    @form(OperationForm)
    def delete(self):
        ids = self.form.ids.data

        excs = {}

        for id in ids:
            try:
                AdminUserService.delete(id)
            except Exception as e:
                excs[id] = str(e)

        if len(excs):
            self.error(*DELETE_FAILED, excs=excs)
        self.success(*DELETE_SUCCESS)
