## 三、数据处理

### 1. 直径与逐差计算

钠光波长取 $\lambda=@@LAMBDA@@\,\mathrm{nm}=@@LAMBDA_MM@@\times10^{-4}\,\mathrm{mm}$。由左右位置读数求暗环直径 $D=\lvert x_{\text{左}}-x_{\text{右}}\rvert$，将第 31—21 环与第 20—10 环依次配对，级次差 $m-n=11$，记 $q_i=D_{m_i}^2-D_{n_i}^2$。

@@TABLE@@

以第 31 环和第 20 环为例：

$$
\begin{aligned}
D_{31}&=\lvert @@LEFT31@@-@@RIGHT31@@\rvert=@@D31@@\,\mathrm{mm},\\
D_{20}&=\lvert @@LEFT20@@-@@RIGHT20@@\rvert=@@D20@@\,\mathrm{mm},\\
q_1&=@@D31@@^2-@@D20@@^2=@@Q1@@\,\mathrm{mm^2}.
\end{aligned}
$$

11 组逐差的平均值为

$$
\bar q=\frac{1}{11}\sum_{i=1}^{11}q_i
=\frac{@@SUMQ@@}{11}=@@MEANQ@@\,\mathrm{mm^2}.
$$

### 2. 曲率半径

由 $D_m^2-D_n^2=4(m-n)\lambda R$，得到

$$
\bar R=\frac{\bar q}{4(m-n)\lambda}
=\frac{@@MEANQ@@}{4\times11\times@@LAMBDA_MM@@\times10^{-4}}\,\mathrm{mm}
=@@R_MM@@\,\mathrm{mm}=@@R_M@@\,\mathrm m.
$$

<!-- pagebreak -->

### 3. A 类标准不确定度

由 11 组逐差结果的离散性，均值的 A 类标准不确定度为

$$
u_A(\bar q)=\sqrt{\frac{\sum_{i=1}^{11}(q_i-\bar q)^2}{11(11-1)}}
=\sqrt{\frac{@@SSQ@@}{110}}\,\mathrm{mm^2}
=@@UQ@@\,\mathrm{mm^2}.
$$

将 $\lambda$ 作为给定常数，按 $\bar R=\bar q/(44\lambda)$ 传播：

$$
u_A(\bar R)=\left\lvert\frac{\partial\bar R}{\partial\bar q}\right\rvert u_A(\bar q)
=\frac{u_A(\bar q)}{44\lambda}
=@@UR_MM@@\,\mathrm{mm}=@@UR_M@@\,\mathrm m.
$$

因此，曲率半径及其 A 类标准不确定度表示为

$$
\boxed{R=(@@R_ROUNDED@@\pm@@UR_ROUNDED@@)\,\mathrm m}
\qquad \frac{u_A(\bar R)}{\bar R}=@@RELATIVE@@\%.
$$

## 四、实验结论及现象分析

牛顿环由空气薄膜上下表面反射光的干涉形成。同一级暗环对应相同空气膜厚度；随级次增大，环半径增大、相邻环间距减小。直径平方的逐差近似恒定，与 $D_m^2-D_n^2=4(m-n)\lambda R$ 相符，可据此测得平凸透镜的曲率半径。

误差主要来自暗环有一定宽度、叉丝定位及调焦视差，以及测微螺杆换向时的空回。读数时应统一瞄准暗纹中心，消除视差并保持单方向移动。采用左右读数之差和固定级次差，可消去共同位置零点及绝对环级数偏移的影响；逐差平均可减小随机读数误差。

## 五、讨论题

### 1. 为什么测量牛顿环直径时，通常选择较大的环级数，而不是只测量靠近中心的几个环？

中心附近易受接触处形变、尘粒及暗斑影响，环级数和位置较难判定。较大级次的直径较大，在相同读数误差下相对误差较小；选取间隔较大的两级暗环，也可增大直径平方差，减小其相对误差。但环级数过大时条纹过密，反而不易瞄准，应选择清晰可辨的暗环。

### 2. 如果将实验中使用的单色光波长增大，在其他条件不变的情况下，牛顿环的半径和环间距将如何变化？

保持曲率半径和所比较的环级次不变，由

$$
r_m=\sqrt{m\lambda R},\qquad
r_{m+1}-r_m=\sqrt{\lambda R}\bigl(\sqrt{m+1}-\sqrt m\bigr),
$$

可知各级暗环半径及相邻暗环间距均随 $\sqrt{\lambda}$ 增大，整个环系向外扩展。
