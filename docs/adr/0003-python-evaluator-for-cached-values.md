# 内置 Python 表达式求值器，负责数值重算与缓存值填充

派生对象的缓存值不由 Builder 手填，也不完全依赖 GeoGebra 加载时重算：ggb_check 内置一个求值器，支持常见函数子集（四则、幂、sqrt/三角/abs/min/max/If 等），用它重算并填充 `<value>`/`<coords>`，同时作为数值一致性校验。算不了的函数写 best-effort 值并依赖 GeoGebra 加载重算兜底。

**Considered Options**：全靠 GeoGebra 重算（省掉求值器，但首屏/缩略图可能显示陈旧值，且失去数值校验手段）；全函数覆盖（成本失控）。**Consequences**：求值器是 M3 的主要工作量；函数子集清单写死在 construction-language.md，超集需求按个案例行扩展。
