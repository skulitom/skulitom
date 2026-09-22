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

When refreshing results, verify the project’s current README and evidence links. Date experimental claims, distinguish the recorded controller from newer results, and check section anchors. Check Primordia’s world and preset counts against its README when updating the profile.

Lead project descriptions with what someone can do or read, then explain the technology. Link LitHarness to the portfolio walkthrough and recorded writing sample. Keep World Language Map, Export Atlas, London in minutes, Chinese Touch Typing, Chinese Radicals, and Keepsake visible as compact illustrated web-app buttons. Do not feature Ganglion, Glossia, or Unsung for now. Keep the portfolio button prominent directly below the header. The earlier Latent Space Explorer experiment may remain in a separate expandable section. The verified professional contact is https://www.linkedin.com/in/artem-skulimovskiy-7bb028118/.

Run `python scripts/generate_pixel_buttons.py` to rebuild the compact web-app buttons and main portfolio button in `assets/links/v3/`. Keep each button as its own linked image, so they wrap naturally on narrower screens. Artem prefers a pixelated retro aesthetic with detailed but restrained motion. Each original pixel scene animates briefly during a 24-second cycle; web-app start times are staggered by four seconds. Labels and frames stay still. Each button uses a `<picture>` source to serve a matching motionless SVG from `assets/links/v3/static/` when reduced motion is preferred. The animated files also contain a reduced-motion CSS guard. GitHub profile images do not support custom hover interactions; reserve those for a future website update. The original static v1 artwork and generator remain for cached pages. Use a new version directory if changing published artwork.

Use the header’s dark violet/navy panels, rounded frames, and Segoe UI labels for link buttons; keep the retro character in the small animated pixel scenes. Avoid a solid mint portfolio block or stepped button frames. Web-app tiles have a 136 px intrinsic width and a 112 px variant below 375 px viewport width, so two fit in GitHub’s narrow README column. Do not add a fixed width attribute to these images, which would override the responsive picture source dimensions. Keep both narrow and regular still-image sources for reduced motion.
