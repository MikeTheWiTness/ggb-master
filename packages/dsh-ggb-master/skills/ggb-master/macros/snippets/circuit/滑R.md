# 直抄片段：滑R（源：宏库 .ggt）

- 用途：滑R[ <Point>, <Point> ]
- 输入 2 个 → 输出 13 个（输出对象按需保留/隐藏）。
- 已知坑：原宏用 PointIn 随机点，每次导入外观不同；本片段已确定性化（Point[路径, 0.5]）。
- **多片段同用时**：把下面的 `hr2_` 全局替换为你项目内的唯一前缀，防标签冲突。
- 输入对象：片段自带输入定义（label 带 `hr2_` 前缀）；替换 label 时同步替换片段内引用。

## XML 片段（贴进 <construction> 末尾）

```xml
<element type="point" label="hr2_A_8"><show object="true" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelOffset x="-15" y="-12" /><labelMode val="0" /><animation step="0.1" speed="1" type="1" playing="false" /><pointSize val="4" /><pointStyle val="10" /><coords x="8" y="1" z="1" /></element>
<element type="point" label="hr2_B_8"><show object="true" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="0.1" speed="1" type="1" playing="false" /><pointSize val="4" /><pointStyle val="10" /><coords x="9" y="1" z="1" /></element>
<command name="Segment"><input a0="hr2_A_8" a1="hr2_B_8" /><output a0="hr2_q_7" /></command>
<element type="segment" label="hr2_q_7"><show object="false" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" opacity="178" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="1" z="-1" /></element>
<command name="Point"><input a0="hr2_q_7" /><output a0="hr2_C_7" /></command>
<element type="point" label="hr2_C_7"><show object="true" label="false" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="10" /><coords x="8.49966097152124" y="1" z="1" /></element>
<command name="Circle"><input a0="hr2_C_7" a1="1" /><output a0="hr2_d_6" /></command>
<element type="conic" label="hr2_d_6"><show object="false" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" opacity="178" /><eqnStyle style="specific" /><eigenvectors x0="1" y0="0" z0="1.0" x1="0" y1="1" z1="1.0" /><matrix A0="1" A1="1" A2="72.2442366308014" A3="0" A4="-8.49966097152124" A5="-1" /></element>
<command name="Point"><input a0="hr2_d_6" a1="0.5" /><output a0="hr2_E_6" /></command>
<element type="point" label="hr2_E_6"><show object="true" label="false" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="10" /><coords x="8.680692101604016" y="0.9508981204544509" z="1" /></element>
<command name="Segment"><input a0="hr2_A_8" a1="hr2_B_8" /><output a0="hr2_r_9" /></command>
<element type="segment" label="hr2_r_9"><show object="false" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" opacity="178" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="1" z="-1" /></element>
<command name="Mirror"><input a0="hr2_E_6" a1="hr2_r_9" /><output a0="hr2_F_6" /></command>
<element type="point" label="hr2_F_6"><show object="false" label="true" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><pointSize val="5" /><pointStyle val="10" /><coords x="8.680692101604016" y="1.0491018795455491" z="1" /></element>
<command name="Mirror"><input a0="{hr2_E_6, hr2_F_6}" a1="hr2_C_7" /><output a0="hr2_l1_2" /></command>
<element type="list" label="hr2_l1_2"><show object="false" label="true" ev="4" /><objColor r="0" g="100" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><pointSize val="5" /><pointStyle val="0" /><angleStyle val="0" /></element>
<command name="Point"><input a0="hr2_l1_2" /><output a0="hr2_G_7" /></command>
<element type="point" label="hr2_G_7"><show object="false" label="true" ev="4" /><objColor r="255" g="153" b="51" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="0" /><coords x="8.318629841438465" y="0.9508981204544509" z="1" /></element>
<command name="Point"><input a0="hr2_l1_2" /><output a0="hr2_H_7" /></command>
<element type="point" label="hr2_H_7"><show object="false" label="true" ev="4" /><objColor r="255" g="153" b="51" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="0" /><coords x="8.318629841438465" y="1.0491018795455491" z="1" /></element>
<command name="Segment"><input a0="hr2_G_7" a1="hr2_H_7" /><output a0="hr2_s_9" /></command>
<element type="segment" label="hr2_s_9"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="-0.09820375909109824" y="0" z="0.8169207209166442" /></element>
<command name="Segment"><input a0="hr2_H_7" a1="hr2_F_6" /><output a0="hr2_e_6" /></command>
<element type="segment" label="hr2_e_6"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="0.3620622601655512" z="-0.37984019765218946" /></element>
<command name="Segment"><input a0="hr2_F_6" a1="hr2_E_6" /><output a0="hr2_g_4" /></command>
<element type="segment" label="hr2_g_4"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0.09820375909109824" y="0" z="-0.8524765958899216" /></element>
<command name="Segment"><input a0="hr2_E_6" a1="hr2_G_7" /><output a0="hr2_i_4" /></command>
<element type="segment" label="hr2_i_4"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelOffset x="-58" y="3" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="-0.3620622601655512" z="0.34428432267891207" /></element>
<command name="Intersect"><input a0="hr2_r_9" a1="hr2_s_9" /><output a0="hr2_I_7" /></command>
<element type="point" label="hr2_I_7"><show object="false" label="true" ev="4" /><objColor r="0" g="102" b="153" alpha="0" /><layer val="4" /><labelMode val="0" /><pointSize val="4" /><pointStyle val="0" /><coords x="0.8169207209166442" y="0.09820375909109824" z="0.09820375909109824" /></element>
<command name="Intersect"><input a0="hr2_r_9" a1="hr2_g_4" /><output a0="hr2_N_4" /></command>
<element type="point" label="hr2_N_4"><show object="false" label="true" ev="4" /><objColor r="0" g="102" b="153" alpha="0" /><layer val="4" /><labelMode val="0" /><pointSize val="4" /><pointStyle val="0" /><coords x="0.8524765958899216" y="0.09820375909109824" z="0.09820375909109824" /></element>
<command name="If"><input a0="Distance[hr2_B_8, hr2_N_4] &lt; Distance[hr2_B_8, hr2_I_7]" a1="Segment[hr2_B_8, hr2_N_4]" a2="Segment[hr2_B_8, hr2_I_7]" /><output a0="hr2_j_4" /></command>
<element type="segment" label="hr2_j_4"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="-0.3193078983959676" z="0.3193078983959676" /></element>
<command name="If"><input a0="Distance[hr2_A_8, hr2_I_7] &lt; Distance[hr2_A_8, hr2_N_4]" a1="Segment[hr2_A_8, hr2_I_7]" a2="Segment[hr2_A_8, hr2_N_4]" /><output a0="hr2_k_4" /></command>
<element type="segment" label="hr2_k_4"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="0.3186298414384705" z="-0.3186298414384705" /></element>
<command name="Point"><input a0="hr2_e_6" /><output a0="hr2_D_3" /></command>
<element type="point" label="hr2_D_3"><show object="true" label="false" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="10" /><coords x="8.441900215031668" y="1.0491018795455493" z="1" /></element>
<command name="OrthogonalLine"><input a0="hr2_D_3" a1="hr2_e_6" /><output a0="hr2_l_2" /></command>
<element type="line" label="hr2_l_2"><show object="false" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" opacity="178" /><eqnStyle style="implicit" /><coords x="-0.3620622601655512" y="0" z="3.0564934719464185" /></element>
<command name="Point"><input a0="hr2_l_2" /><output a0="hr2_J_3" /></command>
<element type="point" label="hr2_J_3"><show object="true" label="false" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="10" /><coords x="8.441900215031668" y="1.4015495803525808" z="1" /></element>
<command name="OrthogonalLine"><input a0="hr2_J_3" a1="hr2_l_2" /><output a0="hr2_m_2" /></command>
<element type="line" label="hr2_m_2"><show object="false" label="true" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" opacity="178" /><eqnStyle style="implicit" /><coords x="0" y="-0.3620622601655512" z="0.5074482087965352" /></element>
<command name="Point"><input a0="hr2_m_2" /><output a0="hr2_K_3" /></command>
<element type="point" label="hr2_K_3"><show object="true" label="false" ev="4" /><objColor r="255" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><animation step="1" speed="1" type="1" playing="false" /><pointSize val="5" /><pointStyle val="10" /><coords x="9.004939225097852" y="1.4015495803525808" z="1" /></element>
<command name="Segment"><input a0="hr2_K_3" a1="hr2_J_3" /><output a0="hr2_n_2" /></command>
<element type="segment" label="hr2_n_2"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelOffset x="-25" y="76" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><outlyingIntersections val="false" /><keepTypeOnTransform val="true" /><startStyle val="default" /><endStyle val="default" /><coords x="0" y="-0.5630390100661842" z="0.7891270882803934" /></element>
<command name="Vector"><input a0="hr2_J_3" a1="hr2_D_3" /><output a0="hr2_v" /></command>
<element type="vector" label="hr2_v"><show object="true" label="false" ev="4" /><objColor r="0" g="0" b="0" alpha="0" /><layer val="4" /><labelMode val="0" /><lineStyle thickness="5" type="0" typeHidden="1" /><coordStyle style="cartesian" /><startPoint exp="hr2_J_3" /><coords x="0" y="-0.35244770080703147" z="0" /></element>
```

## 取用步骤

1. 把 XML 片段贴进目标 geogebra.xml 的 `</construction>` 之前。
2. 若与其它片段共用，先全局替换 `hr2_` 为唯一前缀。
3. 跑 `ggb_check.py <项目>/geogebra.xml --fix` 填缓存；再 `ggb_pack.py` 打包。
