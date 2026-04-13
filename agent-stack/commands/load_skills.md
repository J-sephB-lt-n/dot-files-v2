---
name: load-skills
description: Load agent skills explicitly from a specific folder
---

Now do the following:

1. Ask the user which folder of skills they want to be loaded.
2. List the paths of all files with name `SKILL.md` in that folder using:

   ```bash
   find "{{root-skills-folder-here}}" -type f -name "SKILL.md"
   ```

3. For each file discovered this way named `SKILL.md`, read only the front-matter using:

   ```bash
   sed -n '1{/^---\s*$/!q}; /^---\s*$/,/^---\s*$/p' {{path/to/SKILL.md}}
   ```

These `SKILLS.md` files are very useful documentation but they are also very long documents, so it's important that you don't read them (aside from their front-matter) unless you encounter a situation in which you require that particular "skill" (knowledge/information).

When you do encounter a task for which the information in one or more of these particular `SKILLS.md` documents is relevant, then read that particular `SKILLS.md` file in full. Any relative paths referred to in that `SKILLS.md` are relative to the location of that `SKILLS.md` file - again, only read these files if you consider them relevant to your task after reading the `SKILLS.md`.
