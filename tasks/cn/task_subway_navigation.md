---
id: task_subway_navigation
name: 纽约地铁导航
category: 生产力
scene: 内容创作、PPT、网页与多媒体生成
sub_scene: 交通路线规划
difficulty: L2
capabilities:
- 指令遵循与约束理解
- 数据提取与处理
- 多步推理
- 自然语言生成
- 输出格式适配
grading_type: llm_judge
timeout_seconds: 180
workspace_files:
  - path: "subway_map.md"
    content: |
      # NYC Subway — Simplified Route Map

      This is a simplified representation of key NYC subway lines and their major stops.
      Use this to plan routes between stations.

      ## Line 1 (Red — Local)
      Van Cortlandt Park-242 St → 238 St → 231 St → Marble Hill-225 St → 215 St → 207 St → Dyckman St → 191 St → 181 St → 168 St → 157 St → 145 St → 137 St-City College → 125 St → 116 St-Columbia University → Cathedral Pkwy-110 St → 103 St → 96 St → 86 St → 79 St → 72 St → 66 St-Lincoln Center → 59 St-Columbus Circle → 50 St → Times Sq-42 St → 34 St-Penn Station → 28 St → 23 St → 18 St → 14 St-7th Ave → Christopher St-Sheridan Sq → Houston St → Canal St → Franklin St → Chambers St → Cortlandt St-WTC → Rector St → South Ferry

      ## Line 2 (Red — Express)
      Wakefield-241 St → Nereid Ave → 233 St → 225 St → 219 St → Gun Hill Rd → Burke Ave → Allerton Ave → Pelham Pkwy → Bronx Park East → E 180 St → West Farms Sq-E Tremont Ave → 174 St → Freeman St → Simpson St → Intervale Ave → Prospect Ave → Jackson Ave-Westchester Ave → 149 St-Grand Concourse → 135 St → 125 St → 116 St → Central Park North-110 St → **96 St** → **72 St** → **Times Sq-42 St** → **34 St-Penn Station** → **14 St-7th Ave** → **Chambers St** → Fulton St → Wall St → Clark St → Borough Hall → Hoyt St → Nevins St → Atlantic Ave-Barclays Ctr → Bergen St → Grand Army Plaza → Eastern Pkwy-Brooklyn Museum → Franklin Ave-Medgar Evers College → President St-Medgar Evers College → Sterling St → Winthrop St → Church Ave → Beverly Rd → Newkirk Ave-Little Haiti → Flatbush Ave-Brooklyn College

      ## Line 4 (Green — Express)
      Woodlawn → Mosholu Pkwy → Bedford Park Blvd → Kingsbridge Rd → Fordham Rd → 183 St → Burnside Ave → 176 St → Mt Eden Ave → 170 St → 167 St-Yankee Stadium → 161 St-Yankee Stadium → 149 St-Grand Concourse → 125 St → **86 St** → **59 St** → Grand Central-42 St → **14 St-Union Sq** → Brooklyn Bridge-City Hall → Fulton St → Wall St → Borough Hall → Atlantic Ave-Barclays Ctr → Nevins St → → Crown Hts-Utica Ave

      ## Line 7 (Purple)
      Flushing-Main St → Mets-Willets Point → Junction Blvd → 90 St-Elmhurst Ave → 82 St-Jackson Hts → 74 St-Broadway → 69 St → Woodside-61 St → 52 St → 46 St-Bliss → 40 St-Lowery → 33 St-Rawson → Queensboro Plaza → Court Sq → Hunters Point Ave → Vernon Blvd-Jackson Ave → Grand Central-42 St → Times Sq-42 St → 34 St-Hudson Yards

      ## Line A (Blue — Express)
      Inwood-207 St → Dyckman St → 190 St → 181 St → 175 St → 168 St → 145 St → **125 St** → **59 St-Columbus Circle** → **42 St-Port Authority** → **34 St-Penn Station** → **14 St-8th Ave** → West 4 St-Washington Sq → Spring St → Canal St → Fulton St → High St → Jay St-MetroTech → Hoyt-Schermerhorn → Lafayette Ave → Clinton-Washington Aves → → Far Rockaway / Lefferts Blvd / Rockaway Park

      ## Line L (Gray)
      8 Ave-14 St → 6 Ave-14 St → Union Sq-14 St → 3 Ave → 1 Ave → Bedford Ave → Lorimer St → Graham Ave → Grand St → Montrose Ave → Morgan Ave → Jefferson St → DeKalb Ave → Myrtle-Wyckoff → Halsey St → Wilson Ave → Bushwick Ave → Broadway Junction → Atlantic Ave → Sutter Ave → Livonia Ave → New Lots Ave → East 105 St → Canarsie-Rockaway Pkwy

      ## Transfer Stations (key connections)
      - **Times Sq-42 St**: 1, 2, 3, 7, N, Q, R, W, S, A, C, E
      - **14 St-Union Sq**: 4, 5, 6, L, N, Q, R, W
      - **59 St-Columbus Circle**: 1, 2, A, B, C, D
      - **Grand Central-42 St**: 4, 5, 6, 7, S
      - **Fulton St**: 2, 3, 4, 5, A, C, J, Z
      - **Atlantic Ave-Barclays Ctr**: 2, 3, 4, 5, B, D, N, Q, R
      - **14 St-7th Ave / 14 St-8th Ave**: Connected via walkway (1, 2, 3 ↔ A, C, E, L)
      - **34 St-Penn Station**: 1, 2, 3, A, C, E
      - **Jay St-MetroTech**: A, C, F, R
      - **125 St**: 1 (Broadway), 2/3 (Lenox), A/B/C/D (St. Nicholas), 4/5/6 (Lexington — separate station at 125 St)
      - **168 St**: 1, A, C
---

## Prompt

使用 `subway_map.md` 中提供的地铁图，为以下路线给出导航：

**起点：** Bedford Ave 站（L 线，威廉斯堡，布鲁克林）
**终点：** Yankee Stadium（161 St-Yankee Stadium，4 线，布朗克斯）

请提供：

1. **分步导航**，包含具体的线路和换乘站
2. 每一段的**预计站数**
3. **预计总行程时间**（假设每站 2-3 分钟，每次换乘 5-10 分钟）
4. **备选路线**（如果存在）
5. **小贴士** —— 换乘时的最佳车厢位置、高峰时段的注意事项

将你的导航保存到 `subway_directions.md`。

## Expected Behavior

Agent 应当：

1. 读取地铁图文件
2. 规划从 Bedford Ave（L）到 161 St-Yankee Stadium（4）的路线
3. 识别换乘点（可能在 Union Sq 由 L→4 换乘，或在 14 St 接入一条通往 Yankee Stadium 的线路）
4. 计算大致的站数和行程时间
5. 考虑备选路线
6. 将清晰的导航保存到 `subway_directions.md`

最合理的路线包括：
- 从 Bedford Ave 乘 L 线到 Union Sq-14 St（3 站）
- 在 14 St-Union Sq 换乘 4 线（快车）
- 4 线向上城方向开往 161 St-Yankee Stadium

一个备选方案可能涉及：
- 乘 L 线到 14 St，步行至 14 St-7th Ave，搭乘 2 线快车向上城（但若不再换乘一次则无法直达 Yankee Stadium）

## Grading Criteria

- [ ] 文件 `subway_directions.md` 已创建
- [ ] 路线从 Bedford Ave 乘 L 线
- [ ] 将 Union Sq 或 14 St 识别为换乘点
- [ ] 路线通向 161 St-Yankee Stadium
- [ ] 布朗克斯段使用 4 线
- [ ] 提供了站数
- [ ] 估算了行程时间
- [ ] 提出了备选路线
- [ ] 导航清晰且可遵循

## LLM Judge Rubric

### Criterion 1: Route Correctness (Weight: 35%)

**Score 1.0**：主路线正确且最优 —— 从 Bedford Ave 乘 L 线到 Union Sq，换乘 4 线快车向上城到 161 St-Yankee Stadium。换乘站识别准确。没有不可能的或虚构的连接。
**Score 0.75**：路线正确，但可能包含一个次优换乘或小的站名错误。
**Score 0.5**：路线能从起点到终点，但包含一个不必要的换乘或使用了明显次优的路径。
**Score 0.25**：路线有重大错误（方向错误、不可能的换乘），但显示出一定理解。
**Score 0.0**：路线完全错误或缺失。

### Criterion 2: Practical Detail (Weight: 25%)

**Score 1.0**：包含每一段的站数、合理的时间估算（总计约 40-50 分钟）、换乘步行指引（"穿过站台" 还是 "跟随指示牌"）以及高峰时段提示。这些信息对实际进行此行程的人有用。
**Score 0.75**：实用细节良好，存在小的缺漏。时间估算合理。
**Score 0.5**：基本导航，但缺少旅客想要的细节。
**Score 0.25**：实用信息极少。
**Score 0.0**：没有实用细节。

### Criterion 3: Alternative Route (Weight: 20%)

**Score 1.0**：提供了一条合理的备选路线，并说明何时它可能更优（例如 4 线延误时、周末服务变更时）。备选路线根据地图数据确实可行。
**Score 0.75**：提供了一条可行的备选路线，但理由不充分。
**Score 0.5**：提到了备选路线，但可能不是最优或与主路线几乎无差别。
**Score 0.25**：模糊地提及备选方案而无具体内容。
**Score 0.0**：没有备选路线。

### Criterion 4: Map Interpretation (Weight: 20%)

**Score 1.0**：展示出对所提供地铁图的准确阅读。使用正确的站名，正确识别快车与慢车站（地图中加粗 = 快车），并尊重地图中列出的换乘连接。
**Score 0.75**：地图阅读大体准确，存在小错误。
**Score 0.5**：显示出一些地图阅读能力，但有明显错误或混淆。
**Score 0.25**：几乎没有实际阅读所提供地图的证据。
**Score 0.0**：完全忽略地图或严重误读。

## Additional Notes

- 提供了一份基于文本的地铁图，而非图片，以便所有 Agent 都能完成此任务。该地图包含足够的细节来规划路线。
- Line 2 和 Line 4 描述中加粗的站名表示快车站。
- 之所以选择 Bedford Ave → Yankee Stadium 这条路线，是因为它恰好只需要一次换乘，且有明确的最优路径，便于评分。
- Union Sq 的换乘（L → 4）是纽约地铁系统中最知名的连接之一。
- 高峰时段和服务变更提示用于测试 Agent 是否能超越基本路由，提供真正有用的出行建议。
