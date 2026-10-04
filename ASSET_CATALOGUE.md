# Asset catalogue maintenance

Edit `backend/app/core/asset-types.json` to add or update assets. It is the canonical configuration used by API validation; `frontend/lib/asset-types.generated.json` is its browser bundle copy, refreshed by the frontend predev/prebuild scripts. Run `node frontend/scripts/sync-asset-catalogue.js` after editing data and include the generated copy with changes.

Keep existing IDs stable. Names, categories, descriptions, icons, geometry types, aliases and maturity can be extended without adding UI blocks. New types should default to REFERENCE with all engineering capabilities false and supportsGeneration false. Custom Asset stores its own ID and uses the normal project creation endpoint; it does not use an existing engineering generator as a fallback.

Mark capabilities or generation as supported only after implementing and verifying the corresponding tooling. Existing generator-family mappings remain unchanged for the 14 legacy IDs. Generation is restricted in the workspace controls, parameter form, API endpoint and generation service. Catalogue presence alone never enables a generator.

Checks:
- Frontend: `npm test -- lib/asset-types.test.ts`
- Browser: `npm run test:e2e -- e2e/new-project.spec.ts`
- Backend: `.venv/Scripts/python.exe -m pytest tests/test_asset_catalogue.py -q`
