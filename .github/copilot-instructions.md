# Copilot Instructions — gformlib

## Push & Tag ke GitHub

**JANGAN PERNAH** menjalankan `git push` atau `git tag` secara mandiri.
Selalu minta user untuk konfirmasi dan gunakan urutan berikut.

### Aturan wajib — PR dulu, bukan push langsung ke master

Setiap perubahan **wajib melalui Pull Request**. Jangan pernah push langsung ke `master`.

Alurnya:
1. Buat branch: `git checkout -b <nama-branch>`
2. Commit perubahan di branch tersebut
3. Push branch: `git push origin <nama-branch>`
4. Buat PR ke master: `gh pr create --base master --title "..." --body "..."`
5. User review & merge PR di GitHub
6. Setelah PR merged, baru buat tag dan push tag

**Exception:** Push langsung ke `master` hanya boleh untuk commit pertama (initial commit) jika remote masih kosong.

### Urutan wajib sebelum push:

1. Pastikan semua test lulus:
   ```bash
   .venv/bin/pytest tests/ -v
   ```

2. Pastikan versi di `pyproject.toml` sudah diperbarui sesuai tag yang akan dibuat.

3. Commit semua perubahan ke branch `master`:
   ```bash
   git add -A
   git commit -m "<pesan commit>"
   ```

4. Buat tag versi (format: `vX.Y.Z`):
   ```bash
   git tag vX.Y.Z
   ```

5. Push branch dan tag secara bersamaan:
   ```bash
   git push origin master
   git push origin vX.Y.Z
   ```

### Trigger CI/CD per workflow:

| Workflow | Trigger |
|---|---|
| `test.yml` | Push tag `v*.*.*` atau PR ke `master` |
| `docker.yml` | Push tag `v*.*.*` |
| `docs.yml` | Push tag `v*.*.*` (jika ada perubahan di `docs/`, `src/`, dll.) |
| `publish.yml` | Buat GitHub Release dari tag, atau manual dispatch |

### Catatan penting:
- Branch utama adalah `master` (bukan `main`).
- Semua pipeline hanya berjalan saat tag `vX.Y.Z` di-push — tidak ada auto-build di setiap commit.
- Untuk publish ke PyPI, buat **GitHub Release** dari tag yang sudah ada di GitHub.
- Untuk publish ke TestPyPI, gunakan manual workflow dispatch di tab Actions.
- `docs.yml` trigger build RTD via API (`RTD_TOKEN` secret) — bukan webhook.
- RTD token disimpan sebagai GitHub secret `RTD_TOKEN`, bukan `RTD_WEBHOOK_TOKEN`.
