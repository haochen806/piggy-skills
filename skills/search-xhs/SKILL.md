---
name: search-xhs
description: 搜索和浏览小红书内容，做攻略和信息收集。Use when the user asks to "搜小红书", "小红书搜索", "小红书攻略", "search xiaohongshu", "browse redbook", "用小红书查", "小红书帮我做攻略", or wants travel/food/activity recommendations sourced from 小红书.
allowed-tools: WebSearch, WebFetch, Bash(agent-browser:*), Read, Write, mcp__nanoclaw__send_message
---

# 小红书搜索攻略 Skill

搜索小红书公开内容，提取高赞笔记，整理成实用攻略发给用户。

## 重要：搜索方式

小红书网页版会封锁服务器 IP（error 300012），**不能直接用 agent-browser 打开 xiaohongshu.com**。

使用以下替代方案搜索小红书内容：

### 方法一：WebSearch（推荐，最稳定）

通过搜索引擎搜索小红书内容，Google 会缓存并索引笔记内容：

```
WebSearch: site:xiaohongshu.com {关键词}
```

搜索引擎返回的结果通常包含丰富的内容摘要，足够提取有用信息。

### 方法二：多轮搜索

对于复杂攻略，用不同角度搜索 2-3 次：

```
WebSearch: site:xiaohongshu.com {城市} 攻略 必去
WebSearch: site:xiaohongshu.com {城市} 美食 推荐
WebSearch: site:xiaohongshu.com {城市} 避雷 踩坑
```

### 方法三：通用搜索补充

如果 site:xiaohongshu.com 结果不够，用通用搜索补充：

```
WebSearch: {关键词} 小红书 攻略 推荐 2026
```

## 核心流程

### Step 1: 理解用户需求

从用户消息中提取：
- **搜索关键词**（如 "西雅图周末活动"、"东京美食推荐"）
- **目的类型**（旅游攻略、美食推荐、购物指南、活动推荐、生活技巧等）
- **特殊要求**（预算、时间、偏好等）

### Step 2: 多角度搜索

根据目的类型，组合 2-3 组搜索关键词：

**旅游攻略：**
```
WebSearch: site:xiaohongshu.com {城市} 攻略 必去
WebSearch: site:xiaohongshu.com {城市} 小众 景点
WebSearch: site:xiaohongshu.com {城市} 行程 天
```

**美食推荐：**
```
WebSearch: site:xiaohongshu.com {城市} 美食 必吃 推荐
WebSearch: site:xiaohongshu.com {城市} 餐厅 排名
WebSearch: site:xiaohongshu.com {城市} {菜系} 推荐
```

**活动推荐：**
```
WebSearch: site:xiaohongshu.com {城市} 周末 活动
WebSearch: site:xiaohongshu.com {城市} 好玩 打卡
```

**购物/测评：**
```
WebSearch: site:xiaohongshu.com {品类} 推荐 测评
WebSearch: site:xiaohongshu.com {品类} 避雷 踩坑
```

### Step 3: 提取和交叉验证

从搜索结果中提取：
- 具体推荐（地点、餐厅、活动、产品）
- 实用信息（价格、地址、营业时间、交通）
- 用户评价和避雷提示
- 多篇笔记共同推荐的内容（更可靠）

**交叉验证原则：**
- 多篇笔记提到 = 更可靠
- 注意区分广告/推广和真实推荐
- 关注负面评价和避雷信息
- 优先近期内容

### Step 4: 整理攻略

将收集到的信息整理成结构化攻略。

**输出格式（WhatsApp/Telegram 友好）：**

```
*{攻略主题}* 📍

根据小红书热门笔记整理：

*一、{分类标题}*

1. *{推荐名称}*
   • {关键信息/亮点}
   • 📍 {地址}
   • 💰 {价格}
   • ⏰ {营业时间}
   • 💡 小红书tips: {笔记中的实用建议}

2. *{推荐名称}*
   • ...

*二、{分类标题}*
...

*避雷提醒：*
⚠️ {需要注意的坑}
⚠️ {其他注意事项}

_小贴士：_
• {实用建议 1}
• {实用建议 2}
```

**整理原则：**
- 去重合并：多篇笔记提到的同一推荐合并
- 按推荐度排序：被多篇笔记共同提到的排前面
- 提取实用信息：价格、地址、时间、预约方式
- 包含避雷信息：踩坑经验同样重要
- 分类清晰：按景点/美食/交通/住宿等分类

### Step 5: 发送给用户

用 `send_message` 将整理好的攻略发送。如果内容很长，分 2-3 条发送，每条有独立主题。

## 搜索关键词模板

| 场景 | 搜索关键词组合 |
|------|--------------|
| 城市旅游 | `{城市} 攻略 必去 景点` |
| 美食探店 | `{城市} 美食 必吃 推荐 探店` |
| 周边游 | `{城市} 周边 自驾 一日游` |
| 住宿 | `{城市} 酒店 民宿 推荐 性价比` |
| 购物 | `{城市} 购物 outlet 免税` |
| 亲子 | `{城市} 亲子 带娃 遛娃` |
| 约会 | `{城市} 约会 浪漫 打卡` |
| 产品测评 | `{产品} 测评 推荐 避雷 真实` |
| 穿搭 | `{风格} 穿搭 搭配 推荐` |
| 护肤 | `{肤质} 护肤 推荐 好用` |

## 输出语言

- 默认用中文输出攻略（小红书内容主要是中文）
- 如果用户用英文提问，用英文整理但保留中文原始信息（如店名、地址）
- 保持 WhatsApp/Telegram 格式（不用 markdown heading ##，用 *bold* 和 • 列表）

## Agent-Browser 备用方案

如果未来 XHS IP 限制解除，可以用 agent-browser 直接搜索：

```bash
agent-browser open "https://www.xiaohongshu.com/search_result?keyword={keyword}&source=web_search_result_note"
agent-browser wait --load networkidle
agent-browser snapshot -c -d 4
```

目前此方案因 IP 封锁不可用，仅供参考。
