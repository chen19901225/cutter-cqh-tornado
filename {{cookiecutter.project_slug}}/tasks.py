import json
from invoke import task
import os
proj_dir = os.path.dirname(
    os.path.abspath(__file__)
)
print("proj_dir:{}".format(proj_dir))
env_dir = os.path.join(proj_dir, 'venv')
proj_name = '{{cookiecutter.project_slug}}'
history_path = os.path.join(proj_dir, '.history')

from cqh_util import invoke_util
import git
repo = git.Repo(proj_dir)


@task
def lint_new(c):
    files = invoke_util.git_unstaged_and_untracked_file_list(proj_dir)
    files = [f for f in files if f.endswith(".py")]
    #print(files)
    cmd = f"{env_dir}/bin/flake8 {' '.join(files)}"
    # print("cmd:{}".format(cmd))
    c.run(cmd)


@task
def doc(c):
    with c.cd(f"{proj_dir}/docs"):
        c.run(f"{env_dir}/bin/sphinx-build -M html . _build")


@task
def gpush(c):
    files = invoke_util.git_unstaged_and_untracked_file_list(proj_dir)
    if files:
        repo.index.add(files)
        repo.index.commit("comment")
        repo.remote().push()


@task
def copy_files(c):
    c.run(f'ansible-playbook {proj_dir}/playbooks/copy_files.yaml -e proj_dir={proj_dir} -e proj_name={proj_name}')


def save_file_version(name, version_list):
    old = None
    with open(history_path, 'r') as f:
        old = json.loads(f.read())
    old[name] = version_list
    with open(history_path, 'w') as f:
        f.write(json.dumps(old, indent=2))


def get_file_version(name):
    # print('get_version')
    with open(history_path, 'r') as f:
        content = f.read()
        print('get_version:{}'.format(content))
        return json.loads(content)[name]


def get_base_kwargs():
    d = dict(
        proj_dir=proj_dir,
        proj_name=proj_name,
        process_number=1

    )
    d['max_process_number'] = d['process_number'] - 1
    return d


def get_local_kwargs(**kwargs):
    d = get_base_kwargs()
    if kwargs:
        d.update(kwargs)
    for key, value in d.items():
        print("key:{}, value:{}".format(key, value))
    return d


def get_line_args(kwargs):
    li = []
    for key, value in kwargs.items():
        li.append(" -e {}={} ".format(key, value))
    return "".join(li)


@task(copy_files)
def deploy_local(c):
    deploy_tag = 'local'
    version_list = get_file_version(deploy_tag)
    print(f'version_list, {version_list}')
    version_list[-1] = version_list[-1] + 1
    save_file_version(deploy_tag, version_list)
    print('version_list:{}'.format(version_list))
    tag_name = 'v{}--{}'.format('.'.join(map(str, version_list)),
                                deploy_tag)
    print('tag_name:{}'.format(tag_name))
    kwargs = get_local_kwargs()
    line_kwargs = get_line_args(kwargs)
    ansible_cmd = f'ansible-playbook {proj_dir}/playbooks/deploy_local.yaml {line_kwargs}'
    print('ansible_cmd:{}'.format(ansible_cmd))
    c.run(ansible_cmd)


@task
def deploy_restart(c):
    d = get_local_kwargs()
    line_kwargs = get_line_args(d)
    ansible_cmd = f"ansible-playbook {proj_dir}/playbooks/deploy_local.yaml --tags=supervisor_restart {line_kwargs} "
    c.run(ansible_cmd)


@task
def list_tags(c):
    ansible_cmd = f"ansible-playbook {proj_dir}/playbooks/deploy_local.yaml --list-tags"
    c.run(ansible_cmd)
