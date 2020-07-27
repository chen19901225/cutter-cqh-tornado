# generated_by_dict_unpack:HandlerAdminBase
import os
from tornado import log
from tornado.web import StaticFileHandler

name = 'doc_static'


class HandlerDocStatic(StaticFileHandler,
                       ):

    def initialize(self):
        super().initialize(path=self.settings['doc_root'], default_filename='index.html')

    # def prepare(self):

    #     ret = super().prepare()
    #     log.gen_log.info("self.current_user:{}".format(self.current_user))
    #     if not self.current_user:

    #         self.redirect('/admin?next_url={}'.format(self.request.uri))
    #         raise web.Finish()
    #     return ret

    @classmethod
    def get_absolute_path(cls, root, path):
        """Returns the absolute location of ``path`` relative to ``root``.

        ``root`` is the path configured for this `StaticFileHandler`
        (in most cases the ``static_path`` `Application` setting).

        This class method may be overridden in subclasses.  By default
        it returns a filesystem path, but other strings may be used
        as long as they are unique and understood by the subclass's
        overridden `get_content`.

        .. versionadded:: 3.1
        """
        abspath = os.path.abspath(os.path.join(root, path))
        log.gen_log.info("path:{}, absolute_path:{}".format(path, abspath))
        return abspath
