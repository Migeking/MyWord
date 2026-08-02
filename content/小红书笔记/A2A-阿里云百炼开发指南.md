# 阿里云百炼平台 A2A 三方 Agent 开发避坑指南

## 前言
AI越来越流行，唯有拥抱AI才能焕发新生。拿起 .NET，玩转A2A协议，开发自己的Agent，链接阿里云百炼。

## 认识 A2A 协议
Google 联合多家公司提出的 Agent 互操作协议。核心概念：Agent Card（名片）、Task（工作单元）、Artifact（输出产物）。

## Microsoft.Agents.AI 框架集成
微软官方 A2A SDK，与 Semantic Kernel 同生态，对 ASP.NET Core 原生支持。

## 踩坑记录
- Preview 版本 API 不兼容
- 命名空间变更
- AgentCard JSON 序列化需 CamelCase

## 单 Agent 到多 Agent
独立 TaskManager + 独立路由，互不干扰。

## 调试
Agent Card 浏览器查看，消息用 PostMan 发送 JSON-RPC。

## AI 程序调用
LLM 识别意图，自动调用 Agent。

## 结语
期待阿里云升级 A2A v1.0。
