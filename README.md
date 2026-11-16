# BPA 知识库部署仓库

本仓库存放公司教材（包括草稿及管理员内容）和网站生成代码。仓库协作者可读取 Git 历史，请仅向获授权人员开放。

日常编辑源是原 Obsidian 内容库。回到原项目目录运行 `python3 scripts/prepare_deployment_repository.py`，将源内容同步至此仓库；该脚本不会提交、推送或部署。若本仓库内的同步文件被直接修改，脚本会停止，避免覆盖。

运行 `python3 scripts/build_site.py publish` 生成 `构建结果/发布包/`。只有 status 为 published 的文章进入网站；draft 与 review 不进入正式构建。上传图标仅生成文件，不会上传。

网站部署与仓库访问权限是两个不同问题。连接 EdgeOne 前，应确认受控访问方式并验证；Git 历史含草稿和管理员内容。
