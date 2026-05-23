# Copilot Instructions — gformlib

## Push & Tag ke GitHub

**JANGAN PERNAH** menjalankan `git push` atau `git tag` secara mandiri.
Selalu minta user untuk konfirmasi dan gunakan urutan berikut.

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
