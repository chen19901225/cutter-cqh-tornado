from tornado.options import options
from {{cookiecutter.project_slug}}.run import create_app, run_app, define_options
from tornado.log import gen_log
from {{cookiecutter.project_slug}}.settings import settings

if __name__ == "__main__":
    define_options()
    options.parse_command_line()
    option_dict = options.as_dict()
    gen_log.info("option_dict:{}".format(option_dict))
    app = create_app(**option_dict, **settings)
    run_app(app, options)
