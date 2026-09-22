# Editing this profile

The root README appears on [github.com/skulitom](https://github.com/skulitom) because this public repository has the same name as the account.

- Edit `README.md` to change the introduction, project links, or toolkit.
- Keep the animated illustrations and grouped custom skill pills when refreshing profile content; Artem explicitly prefers this visual style.
- Keep LitHarness first as the main project, and use the latest Liftoff recording for Haltere's preview.
- Do not feature open-source contributions in the profile or portfolio; Artem prefers to leave them out.
- Edit `scripts/generate_assets.py` and run `python scripts/generate_assets.py` to regenerate the illustrations.
- Commit the generated `assets/v2/*.svg` alongside the script.
- Run `python scripts/generate_badges.py` to rebuild the toolkit badges in `assets/toolkit/v1/` from the local icon data.

All graphics are SVG, stored in this repository. The header and project illustrations are original; the toolkit badges use Simple Icons 16.30.0 brand marks, with original terminal and database symbols for Codex and SQL. The icon source and CC0 license are included in `assets/toolkit/`.

The graphics need no image services, API keys, scheduled workflows, external fonts, or JavaScript. Animations respect the viewer's reduced-motion preference. Browsers without animation support still show complete static artwork. The header has a separate layout for narrow screens; toolkit badges wrap individually to fit the available width.

The project illustrations are decorative representations, not screenshots, live activity, contribution statistics, or project status indicators.

GitHub documentation: [Managing your profile README](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme).

When changing graphics, use a new version directory and update the README image paths so browsers do not reuse an older cached image.

When refreshing results, verify the project’s current README and evidence links. Date experimental claims, distinguish the recorded controller from newer results, and check section anchors. The 22 September 2026 refresh adds Ganglion, Glossia, Keepsake, Unsung, and World Language Map; Primordia has five worlds and 42 presets.

Lead project descriptions with what someone can do or read, then explain the technology. Link LitHarness to the portfolio walkthrough and recorded writing sample. Keep the four supporting agent/tool projects visible and the six maps, learning tools and earlier experiments in the expandable section. The verified professional contact is https://www.linkedin.com/in/artem-skulimovskiy-7bb028118/.
