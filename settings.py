import yaml
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    num_students: int
    cpu: str
    memory: str
    base_port: int
    auth_port: int
    nginx_port: int
    image: str
    data_dir: str
    workspaces_dir: str
    admin_password: str


def load_config(path: str = "config.yml") -> Config:
    with open(path) as f:
        data = yaml.safe_load(f)
    return Config(
        num_students=data["num_students"],
        cpu=data["cpu"],
        memory=data["memory"],
        base_port=data["base_port"],
        auth_port=data["auth_port"],
        nginx_port=data["nginx_port"],
        image=data["image"],
        data_dir=data["data_dir"],
        workspaces_dir=data["workspaces_dir"],
        admin_password=data.get("admin_password", "admin"),
    )
