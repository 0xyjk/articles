---
title: 从噪声到视频：视频生成的第一性原理
cover: ../../assets/understanding-comfyui/03-first-principles-of-video-generation/cover.png
---

# 从噪声到视频：视频生成的第一性原理

> ComfyUI 很适合拿来观察视频工作流，但这篇文章真正想讲的，还是它背后的通用原理。

这一轮视频模型真正出圈，不是因为它突然能动了，而是因为它开始像一段真正的视频了。

镜头会推拉，人物不会每一帧都换脸，动作衔接也更自然。以 ByteDance 的 [Seedance 2.0](https://seed.bytedance.com/en/seedance2_0) 为例，官方已经不再只强调“能生成视频”，而是在强调多模态输入、音视频联合生成，以及更细的镜头控制。

这说明一件事：视频生成的问题，早就不是“让图片动起来”这么简单。

如果你已经看过上一篇《从噪声到图像：图片生成的第一性原理》，这一篇就是它的下一步。图片生成解决的是“这一帧像不像”。视频生成还要多解决一个问题：**前后帧是不是同一个世界。**

所以这篇文章不打算先教你怎么搭 ComfyUI 节点，也不打算先讲哪个模型最强。我想先把一件更重要的事讲清楚：文生视频、图生视频、视频转视频，这几类工作流到底共享什么基本链路，以及这条链路到了视频之后，为什么会突然难很多。

## 一张图先看懂

如果先不看具体节点名，只抓主干，视频生成也可以先压缩成这样：

`CONDITIONING + VIDEO LATENT -> Video Generator / Sampler -> VIDEO LATENT -> Video Decoder -> VIDEO`

它和上一篇的图像链路其实很像。只是现在那块“画布”不再是一张静态 latent，而是一段沿时间展开的 latent 序列。

你可以先把它理解成：图片生成是在一块压缩画布上修一张图，视频生成是在一段压缩过的时空画布上修一串彼此相关的帧。

这个说法不是比喻硬凑出来的。NVIDIA 在 `2023-06-20` 发布的 Video LDM 工作，讲的就是把图像 latent diffusion 扩展到视频：先继承图像 LDM 的能力，再把时间维度引进 latent diffusion 过程。[Video LDM](https://research.nvidia.com/publication/2023-06_align-your-latents-high-resolution-video-synthesis-latent-diffusion-models)

OpenAI 在 `2024-02-15` 发布的 Sora technical report 里也用了类似思路。它先把视频压进 latent space，再切成 spacetime patches 来训练模型，而且直接把图片描述成 **single-frame video**。[Sora technical report](https://openai.com/research/video-generation-models-as-world-simulators)

所以先记住一个判断：

**视频生成不是另一套完全不同的宇宙。它延续了图片生成的主链路，只是把时间也拉进了生成过程。**

## 视频不是多几帧，而是多了一条时间轴

很多人第一次理解视频生成时，直觉会说：图片生成是一张图，视频生成就是很多张图连起来。

这个直觉不能说全错，但只说对了一半。

如果你真的只是独立生成很多张图，再把它们拼起来，最常见的结果不是“视频”，而是“会闪的幻灯片”。人物脸会跳，衣服纹理会变，背景里刚才还在的杯子下一帧就没了，镜头运动也会断。

问题就出在这里。

图片生成只需要回答一个问题：这一帧像不像。

视频生成要同时回答两个问题：

- 这一帧像不像
- 下一帧和上一帧之间，还是不是同一个对象、同一个场景、同一个动作过程

这第二个问题，就是 **时间一致性**。

Sora technical report 在讲视频生成难点时，明确提到了 temporal consistency、long-range coherence 和 object permanence。[Sora technical report](https://openai.com/research/video-generation-models-as-world-simulators)

翻成人话就是：

- 角色不能一会儿像这个人，一会儿像另一个人
- 场景里的物体不能无缘无故消失或变形
- 一个动作要能跨很多帧维持逻辑

所以我更愿意把视频生成理解成：**在生成单帧质量之外，再额外维护时间上的因果和连续性。**

也正因为这样，视频模型的难点从来不只是分辨率和时长，而是“这段时间里，世界有没有崩掉”。

如果你对上一篇里的 `latent` 已经有点模糊了，可以先临时把它重新理解成“压缩后的内部画布”。到了视频里，变化并不是这个概念被推翻了，而是这块画布从静态二维，变成了沿时间展开的时空画布。

但这里还有一个更现实的问题：就算模型知道要维持时间一致性，它也不可能在海量原始像素上直接硬修。

于是问题就变成了：视频生成真正发生在哪里？

## 为什么视频生成的主战场也不在像素空间

上一篇我们已经讲过，图片生成通常不直接在像素空间做去噪，而是先进 latent 空间。

视频上这个道理只会更成立，不会更弱。

原因很简单：视频的数据量太大了。

一张图片已经是二维像素网格。视频再往上多一维时间，计算量会立刻膨胀。如果还想做高分辨率、长时长、多轮采样，直接在原始像素上硬算，成本会非常夸张。

所以主流路线也会先压缩，再生成。

Sora technical report 的原话很关键：视频会先被压缩到 latent space，而且这种压缩同时发生在 **temporal** 和 **spatial** 两个方向。[Sora technical report](https://openai.com/research/video-generation-models-as-world-simulators)

这句话很值得停一下。

图片里的 latent，主要是在压缩空间信息。视频里的 latent，不只是压缩空间，还在压缩时间。也就是说，模型不是直接盯着一帧一帧的原始像素去想问题，而是在一个更紧凑的时空表示里工作。

这样做的好处也很直接：

- 计算成本更低
- 长视频生成更可行
- 时序建模更容易和主干模型整合

所以如果你后面在 ComfyUI 里看到 video latent、clip 采样、frame 数、context window 这些概念，不要先把它们理解成零碎参数。它们本质上都在服务同一件事：让模型能在时空 latent 上工作。

## CONDITIONING 到了视频，不再只有 prompt

在图片生成里，`CONDITIONING` 最常见的来源是 prompt，也就是文字条件。

到了视频，这件事立刻变复杂了。

因为你想控制的东西变多了。你不只想说“画一只猫”，你还想说：

- 这只猫往哪边走
- 镜头怎么移动
- 节奏快一点还是慢一点
- 参考图里的人物长相要不要保留
- 参考视频里的动作轨迹要不要继承

于是视频生成里的 `CONDITIONING`，通常不再只是文字，而是可能包含文字、图像、视频，甚至音频。

ByteDance 在 [Seedance 2.0](https://seed.bytedance.com/en/seedance2_0) 的官方介绍里，明确把输入形式写成 text、image、audio、video 的组合。它强调的也不只是“能听懂 prompt”，而是 unified multimodal audio-video joint generation architecture。

这背后的意思很明确：视频生成里的条件控制，已经从“给一句描述”变成“给一组约束”。

不过这篇先收一收边界。我们主要讲的是视频生成的视觉主干。音频当然也可以进入系统，而且像 Seedance 这类模型已经在往音视频联合生成上走，但那是再往后的一层扩展。就这篇来说，你先把它理解成“条件输入可以越来越丰富”，就够了。

如果你把这件事放回工作流里看，会更容易理解。

在图片里，`CONDITIONING` 更像一句创作指令。

在视频里，`CONDITIONING` 更像一份拍摄 brief。里面不只是主题，还可能带着角色设定、动作意图、镜头语言，甚至声音线索。

## Video Generator / Sampler 处理的是时空去噪

现在来到主链路的中心：`Video Generator / Sampler`。

如果沿用上一篇的说法，它仍然是整套系统里真正负责生成的模块。前面的模块都在做准备，真正把噪声一步步修成结果的，还是它。

但这里有一个决定性的变化。

图片里的 Sampler，处理的是一张 latent 画布。

视频里的 Sampler，处理的是一段沿时间展开的 latent 序列。

这意味着它每一步做的都不只是“把这一帧修得更像”，还要同时处理“这一帧和前后帧怎么连起来”。你可以把它理解成：模型不只在修画面本身，也在修帧与帧之间的关系。

这也是为什么视频模型里经常会看到 temporal layer、3D 结构、spacetime patch、video transformer 这些词。它们名字不同，想解决的问题却很一致：让生成过程能真正看见时间。

NVIDIA 的 Video LDM 用的是在图像 LDM 上追加 temporal layers 的思路。[Video LDM](https://research.nvidia.com/publication/2023-06_align-your-latents-high-resolution-video-synthesis-latent-diffusion-models)

Sora technical report 则把视频表示成 spacetime patches，再交给 diffusion transformer 去建模。[Sora technical report](https://openai.com/research/video-generation-models-as-world-simulators)

底层实现可以不同，但第一性原理是同一个：

**视频生成不是逐帧各算各的，而是在一个时空联合表示里逐步去噪。**

## VIDEO LATENT：生成真正发生的时空画布

如果说上一篇里的 `LATENT` 是压缩后的图像画布，那么这一篇里的 `VIDEO LATENT` 可以先理解成：

**压缩后的时空画布。**

它不是一张图，也不是简单堆起来的很多图。

更准确地说，它是一段已经被压缩、重新组织过的视频内部表示。这里面保留了人物、场景、动作、镜头变化这些关键结构，但它已经不是你能直接预览的像素视频。

这个概念很重要。因为很多你以为发生在“视频帧”上的事，其实更早就发生在 `VIDEO LATENT` 上了。

比如：

- 一个角色的轮廓能不能前后稳定
- 镜头推进时背景透视会不会乱
- 转身动作有没有连续性

这些都不是最后导出 MP4 时才决定的，而是在 latent 级别的生成阶段就基本定下来了。

所以从工作流角度看，视频模型并不是最后多一个“导出视频”的步骤，而是从一开始就在处理一块时空 latent 画布。

## 文生视频、图生视频、视频转视频，其实共用一条主干

如果把前面的概念重新放回流程里，你会发现文生视频、图生视频、视频转视频也不是三套完全不同的系统。

它们共享的主干和图片生成非常像：

- 条件输入先变成 `CONDITIONING`
- 主模型负责时空去噪
- `Video Generator / Sampler` 负责逐步采样
- `Video Decoder` 把 latent 结果还原成最终视频

真正不同的地方，主要还是初始 `VIDEO LATENT` 从哪里来，以及条件输入的来源有什么不同。

这里还有一个很自然的问题：如果最后有 `Video Decoder` 把 latent 还原成视频，那输入图片和输入视频一开始又是怎么进来的？

答案是：不同模型和工作流里，这一步的具体名字不完全一样，也不一定总被单独画成一个节点，但本质上都要先把输入压进模型能处理的内部视频表示，再交给后面的采样过程。也就是说，视频工作流里通常也有一座“进去的桥”，只是它不像图片工作流里的 `VAE Encode` 那么经常被统一命名。

文生视频时：

- 你主要给的是文字条件
- 系统从一段初始噪声 latent 开始生成

图生视频时：

- 你通常还会给一张参考图
- 系统要在保留主体外观的同时，让它开始运动

视频转视频时：

- 你已经给了一段已有视频
- 模型更像是在继承原视频结构的基础上重写风格、内容或运动细节

OpenAI 在 Sora technical report 里展示的 image animation、video editing、video extension，本质上都能放回这条主干去理解。[Sora technical report](https://openai.com/research/video-generation-models-as-world-simulators)

这也是为什么我一直觉得，“生视频”和“改视频”没有看起来那么远。它们底层共用的是同一套时空生成逻辑，只是起点和约束不同。

## Video Decoder：把内部结果还原成你能看的视频

上面说了这么多 latent，最后还是要落回你能播放的视频文件。

这时候就轮到 `Video Decoder` 出场了。

它扮演的角色和上一篇里的 `Image Decoder` 一样，都是桥。只是桥的一端不再是静态图像 latent，而是视频 latent。

所以整条链路的最后一步，仍然很朴素：

`VIDEO LATENT -> Video Decoder -> VIDEO`

只有到了这一步，模型内部那段压缩后的时空表示，才会被还原成你能预览、导出、剪辑的视频。

从使用者视角看，最后看到的是一个 mp4、mov 或 gif。

但从系统视角看，真正决定它长什么样的，早就在前面的 latent 采样阶段完成了。

## 把整条链路再翻成人话

现在把这条视频生成链路重新翻译成人话。

第一步，把 prompt、参考图、参考视频，甚至音频，翻译成模型能理解的条件。

`text / image / video / audio -> CONDITIONING`

第二步，准备一块初始的 `VIDEO LATENT` 画布。它可能来自纯噪声，也可能来自输入图像或输入视频编码后的结果。

第三步，让 `Video Generator / Sampler` 开始工作。

它拿着主模型、条件输入和初始时空 latent，一步步去噪，一边生成内容，一边维持时间一致性，最终得到新的 `VIDEO LATENT`。

第四步，把这段内部结果解码回你能看到的视频。

`VIDEO LATENT -> Video Decoder -> VIDEO`

如果你能把这四步在脑子里连起来，后面再学 ComfyUI 里的视频节点，理解会快很多。因为你已经不是在死记模型名和参数名，而是在理解一套完整系统。

上一篇讲的是，图片生成不是“画出来”，而是“修出来”。

这一篇再往前走一步。

视频生成也不是“让图片动起来”，而是**在同一条去噪链路里，额外把时间也一起修出来。**
