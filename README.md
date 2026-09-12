<picture>
  <source media="(max-width: 600px)" srcset="assets/v2/hello-mobile.svg">
  <img src="assets/v2/hello.svg" width="100%" alt="Artem Skulimovskiy — software engineer in London. Backend infrastructure, distributed systems, and applied AI.">
</picture>

I'm a **backend and infrastructure engineer at SimCorp**, based in London. I design and operate distributed calculation infrastructure, from worker coordination and batch scheduling to the data layer and failure investigation.

Previously: **Eigen Technologies · JPMorgan · founder of an education startup.** MEng Computer Science, **UCL**, specialising in AI.

**[LitHarness](https://github.com/skulitom/LitHarness) is my main independent project**, exploring long-running agent workflows and persistent state. My other projects include agent execution environments and learned control systems. I use coding agents throughout development, set the architecture and constraints, and review and verify their work.

**[Portfolio & projects →](https://skulitom.github.io/) · [All repositories](https://github.com/skulitom?tab=repositories)**

## Selected projects

<table>
<tr>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/LitHarness"><img src="assets/projects/litharness.webp" width="100%" alt="LitHarness project artwork: a constellation dragon and an open book."></a>
<h3><a href="https://github.com/skulitom/LitHarness">LitHarness</a> · Main project</h3>
<p>Specialised LLM agents coordinate serial fiction over persistent narrative state and immutable manuscript revisions. Working generation pipeline; literary-quality evaluation remains an open research problem.</p>
<p><strong>Python · Agent orchestration · Persistent state</strong></p>
</td>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/Anode"><img src="assets/projects/anode.svg" width="100%" alt="Anode architecture: separate input sessions for you and an agent on the same Windows machine."></a>
<h3><a href="https://github.com/skulitom/Anode">Anode</a></h3>
<p>A Windows child session for an agent, with its own pointer, focus, CLI, MCP controls, and virtual gamepad. Runs as the same user and can access the same files.</p>
<p><strong>C# · .NET · Windows APIs · MCP</strong></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/haltere"><img src="assets/projects/haltere-liftoff-race.png" width="100%" alt="Haltere in Liftoff: the latest lap-following recording, with live neural activity on the left and the game view on the right."></a>
<h3><a href="https://github.com/skulitom/haltere">Haltere</a></h3>
<p>A connectome-constrained recurrent network trained to control a drone in Liftoff. The latest lap-following controller tracks a taught path at 1.5 m/s with 0.67 m mean error. Research prototype; racing speed remains limited.</p>
<p><strong>PyTorch · Differentiable simulation · 30,000 neurons</strong><br><a href="https://skulitom.github.io/#haltere">Watch the Liftoff flight →</a></p>
</td>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/AgentUI"><img src="assets/projects/agentui.svg" width="100%" alt="AgentUI interaction diagram: an agent opens controls, a person adjusts them, and the response returns as structured state."></a>
<h3><a href="https://github.com/skulitom/AgentUI">AgentUI</a></h3>
<p>An MCP server that lets coding agents ask for decisions through forms, sliders, diffs, and live previews. The agent can continue working while a person adjusts the controls.</p>
<p><strong>TypeScript · React · MCP · WebSockets</strong></p>
</td>
</tr>
<tr>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/primordia"><img src="assets/projects/primordia.webp" width="100%" alt="Actual Primordia simulation output: Physarum, Particle Life, Lenia, and reaction–diffusion."></a>
<h3><a href="https://github.com/skulitom/primordia">Primordia</a></h3>
<p>An interactive GPU artificial-life laboratory: four simulation systems, 36 presets, and headless image and video export.</p>
<p><strong>Rust · wgpu · WGSL</strong><br><a href="https://skulitom.github.io/#primordia">Watch the simulations →</a></p>
</td>
<td width="50%" valign="top">
<a href="https://github.com/skulitom/CathodeDisplay"><img src="assets/projects/cathode.webp" width="100%" alt="Cathode application screenshot with a CRT virtual display and picture controls."></a>
<h3><a href="https://github.com/skulitom/CathodeDisplay">Cathode</a></h3>
<p>A CRT virtual monitor for real Windows applications, with GPU phosphor rendering, scanlines, and glow. Available as a self-contained Windows download.</p>
<p><strong>C# · WPF · GPU shaders</strong><br><a href="https://github.com/skulitom/CathodeDisplay/releases/latest">Download →</a></p>
</td>
</tr>
</table>

## Open-source contribution

**[AnyIO: fix imports with loaders that omit `__file__`](https://github.com/agronholm/anyio/pull/1323) — merged.** Fixed an import failure by extending the existing eager-import fallback, with a regression test that fails without the change.

## More to explore

**Interactive web apps:** [Export Atlas](https://skulitom.github.io/export-atlas/) · [London in minutes](https://skulitom.github.io/london-time-map/) · [Chinese Touch Typing](https://skulitom.github.io/chinese-touch-typing/) · [Chinese Radicals](https://skulitom.github.io/chinese-radicals/)

**Generative-model experiment:** [Latent Space Explorer](https://github.com/skulitom/Latent-Space-Explorer)

**Published Android apps:** [Greek Letters Quiz](https://play.google.com/store/apps/details?id=com.greekletters.quiz) · [Medieval Armor Quiz](https://play.google.com/store/apps/details?id=com.armourquiz.medieval) · [Roman Emperors Quiz](https://play.google.com/store/apps/details?id=com.romanemperor.quiz)

**Core toolkit:** Python · SQL · PostgreSQL · Docker · Linux. Project work also uses TypeScript, React, C#, Rust, and PyTorch.
