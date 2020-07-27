from {{cookiecutter.project_slug}} import exceptions, consts


class MixinModel(object):

    def single_update(self, **kwargs):
        return self.set_by_id(self.id, kwargs)

    def can_be_used(self) -> bool:
        if self.is_removed:
            return False
        if not self.is_active:
            return False
        if self.is_locked:
            return False

    @classmethod
    def select_with_expression(cls, expression_list):
        if expression_list:
            if isinstance(expression_list, (list, tuple)):
                return cls.select().where(*expression_list)
            assert isinstance(expression_list, dict)
            return cls.select().filter(**expression_list)
        else:
            return cls.select()

    @classmethod
    def _get_or_raise(cls, expression_list, error_message=None) -> 'MixinModel':
        if isinstance(expression_list, (list, tuple)):
            record = cls.get_or_none(*expression_list)
        elif isinstance(expression_list, dict):
            record = cls.get_or_none(**expression_list)
        else:
            raise TypeError('expression_list should list tuple or dict not {}'.format(type(expression_list)))
        if record is None:
            raise exceptions.CustomErrorException(
                consts.ErrorCode.RECORD_NOT_FOUND, error_message or "记录未找到"
            )
        return record

    @classmethod
    def _check_not_exists_or_raise(cls, expression_list, error_message):
        assert isinstance(expression_list, (list, tuple)), 'expected expression_list be list or tuple'
        record = cls.get_or_none(*expression_list)
        if record is not None:
            raise exceptions.CustomErrorException(
                consts.ErrorCode.RECORD_HAS_EXISTS, error_message or "记录未找到"
            )

    @classmethod
    def refetch(cls, instance) -> 'MixinModel':
        return cls.get_by_id(instance.id)

    @classmethod
    def unremoved_expression_list(cls):
        return [cls.is_removed == 0]

    @classmethod
    def check_duplicate_and_raise(cls, expression_list, msg=None, exclude_list =(),):
        """

        exclude_list: List[self.mod_cls], 排除的id列表
        """
        li = [*expression_list]
        if exclude_list:
            exclude_id_list = [ele.id for ele in exclude_list]
            li.append(cls.id.not_in(exclude_id_list))
        record = cls.get_or_none(*li)
        if record:
            raise exceptions.CustomErrorException(
                consts.ErrorCode.RECORD_HAS_EXISTS,
                msg=msg
            )

    @classmethod
    def choice_list(cls, key, value, expression_list=(), add_empty=False, empty_value=('', '全部'),
                    key_func=None,
                    value_func=None):

        def keep(x):
            return x

        if key_func is None:
            key_func = keep

        if value_func is None:
            value_func = keep

        out = []
        if add_empty:
            out.append(empty_value)
        if expression_list:
            result = cls.select().where(
                *expression_list
            ).order_by(
                cls.id.desc()
            )
        else:
            result = cls.select().order_by(
                cls.id.desc()
            )

        for ele in result:
            out.append((key_func(getattr(ele, key)),
                        value_func(getattr(ele, value))
                        )
                       )
        return out
