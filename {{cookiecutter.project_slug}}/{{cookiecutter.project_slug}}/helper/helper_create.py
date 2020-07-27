
from {{cookiecutter.project_slug}}.service.service_sina import SSina


def create_from_setting(settings):
    service_sina = SSina(settings['sina_{{cookiecutter.project_slug}}_key'])
    
    return dict(service_sina=service_sina)
