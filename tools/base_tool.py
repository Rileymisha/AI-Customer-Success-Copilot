# -*- coding: utf-8 -*-
"""
工具基类（Base Tool）
=====================

定义所有工具的抽象基类，遵循 LangChain Tool Calling 的设计思想：

每个工具（Tool）是一个独立的功能单元，包含：
- name: 工具名称（唯一标识）
- description: 工具描述（帮助 Agent 理解工具用途）
- parameters: 工具接受的参数列表（JSON Schema 格式）
- run(): 工具的执行逻辑

Agent 根据任务的描述文本，结合工具的 name/description/parameters，
自动决定调用哪些工具、以什么顺序调用。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ToolParameter:
    """
    工具参数描述。

    用于向 Agent 描述工具需要什么输入参数，
    类似 LangChain 的 BaseTool.args_schema。

    属性:
        name: 参数名称
        type: 参数类型（string, number, object 等）
        description: 参数说明
        required: 是否必需
    """
    name: str = ""
    type: str = "string"
    description: str = ""
    required: bool = True


@dataclass
class ToolSpec:
    """
    工具规格说明 - 注册到 Agent 的工具元信息。

    遵循 LangChain Tool Calling 协议：
    - name: 工具名，Agent 用这个名字引用工具
    - description: 工具描述，Agent 根据描述决定是否选用该工具
    - parameters: 参数列表，Agent 知道需要传什么参数

    类似 LangChain 的 Tool 类的 name、description、args_schema。
    """
    name: str = ""
    description: str = ""
    parameters: List[ToolParameter] = field(default_factory=list)


class BaseTool(ABC):
    """
    所有工具的抽象基类。

    子类必须实现:
    - name 属性: 工具的唯一名称
    - description 属性: 工具的功能描述
    - run() 方法: 工具的执行逻辑

    LangChain 对应关系:
        BaseTool.name          → LangChain Tool.name
        BaseTool.description    → LangChain Tool.description
        BaseTool.spec           → LangChain Tool.args_schema
        BaseTool.run()          → LangChain Tool._run()

    使用示例::

        class MyTool(BaseTool):
            @property
            def name(self) -> str:
                return "my_tool"

            @property
            def description(self) -> str:
                return "我的自定义工具"

            def run(self, **kwargs) -> Dict[str, Any]:
                # 执行逻辑
                return {"result": "done"}
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """工具的唯一标识名称。"""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """工具的功能描述（Agent 根据描述决定是否调用此工具）。"""
        ...

    @property
    def spec(self) -> ToolSpec:
        """
        工具的完整规格说明（名称 + 描述 + 参数）。

        Agent 通过 spec 了解工具能做什么、需要什么参数。
        子类可以重写此属性以提供更精确的参数描述。
        """
        return ToolSpec(
            name=self.name,
            description=self.description,
            parameters=[],
        )

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        执行工具逻辑。

        参数:
            **kwargs: 工具需要的输入参数

        返回:
            字典格式的执行结果

        异常:
            ToolError: 工具执行出错时抛出
        """
        ...


class ToolError(Exception):
    """
    工具执行错误。

    当工具执行过程中发生可预期的错误时抛出，
    便于 Agent 捕获并决定是否重试或跳过。
    """
    pass
