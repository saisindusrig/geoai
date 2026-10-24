# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: assistant-ui.spec.ts >> conversation, actions and blocked states 1600
- Location: e2e\assistant-ui.spec.ts:5:37

# Error details

```
Error: expect(locator).toHaveCount(expected) failed

Locator:  getByRole('complementary', { name: 'GeoAI Assistant' })
Expected: 0
Received: 1
Timeout:  5000ms

Call log:
  - Expect "toHaveCount" with timeout 5000ms
  - waiting for getByRole('complementary', { name: 'GeoAI Assistant' })
    13 × locator resolved to 1 element
       - unexpected value "1"

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e5]:
    - banner [ref=e6]:
      - link "GeoAI home" [ref=e7] [cursor=pointer]:
        - /url: /
        - generic "GeoAI" [ref=e8]:
          - img [ref=e9]
          - generic [ref=e11]: GeoAI
      - heading "Foundation integrated study · reference 804" [level=1] [ref=e14]
      - generic [ref=e15]:
        - link "3D Sandbox editor" [ref=e16] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
          - img [ref=e17]
          - text: 3D Sandbox editor
        - link "Projects" [ref=e20] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=e21]:
          - button "Save site geometry" [ref=e22]:
            - img [ref=e23]
            - text: Save site geometry
          - link "Export" [ref=e27] [cursor=pointer]:
            - /url: /projects/805/report
            - button "Export" [ref=e28]:
              - img [ref=e29]
              - text: Export
        - link "New concept" [ref=e32] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=e33]:
            - img [ref=e34]
            - text: New concept
        - link "Open settings" [ref=e35] [cursor=pointer]:
          - /url: /settings
          - img [ref=e36]
    - main [ref=e39]:
      - generic [ref=e42]:
        - generic [ref=e43]:
          - generic "Design workflow" [ref=e47]:
            - button "1 Site" [ref=e48]
            - group [ref=e49]:
              - generic "Workflow help" [ref=e50] [cursor=pointer]
            - group [ref=e51]:
              - generic "2 Create / Import" [ref=e52] [cursor=pointer]
            - button "3 Review 3D" [ref=e53]
            - button "4 Edit" [ref=e54]
            - button "5 Analyze / Results" [ref=e55]
            - button "6 Review" [ref=e56]
            - status [ref=e57]: Saved · v1
            - button "Save model" [disabled]
          - generic [ref=e58]:
            - generic [ref=e59]:
              - generic [ref=e62]:
                - generic:
                  - img
                  - generic: 12.97160° N · 77.59460° E
                - generic [ref=e63]:
                  - generic "Mouse navigation" [ref=e64]:
                    - button "Select" [pressed] [ref=e65]
                    - button "Orbit" [ref=e66]
                    - button "Pan" [ref=e67]
                    - button "Mouse controls" [ref=e68]
                  - generic "Viewport presentation" [ref=e69]:
                    - generic [ref=e70]:
                      - button "Model view" [pressed] [ref=e71]
                      - generic [ref=e72]: /
                      - button "Site view" [ref=e73]
                      - generic [ref=e74]: Illustrative finishes · not material evidence
                    - generic [ref=e75]:
                      - group [ref=e76]:
                        - generic "Standard views" [ref=e77] [cursor=pointer]
                      - button "Focus Structure" [ref=e78]
                      - button "Fit All" [ref=e79]
                      - button "Fit selection" [disabled] [ref=e80]
                      - button "Dimensions off" [ref=e81]
                      - group [ref=e82]:
                        - generic "Display legend" [ref=e83] [cursor=pointer]
                  - generic [ref=e85]:
                    - generic "3D workspace viewport" [ref=e88]
                    - button "Full screen" [ref=e90] [cursor=pointer]
              - complementary "Workspace tools" [ref=e94]:
                - group "Object editing" [ref=e95]:
                  - generic [ref=e96]: Edit
                  - generic "Click to select and inspect · Ctrl to add · V" [ref=e97]:
                    - button "Select object" [pressed] [ref=e98]:
                      - img [ref=e99]
                    - generic [ref=e101]: Click to select and inspect · Ctrl to add · V
                  - generic "Move selection · Select an editable object first" [ref=e102]:
                    - button "Move selection" [disabled] [ref=e103]:
                      - img [ref=e104]
                    - generic [ref=e109]: Move selection · Select an editable object first
                  - generic "Rotate selection · Select an editable object first" [ref=e110]:
                    - button "Rotate selection" [disabled] [ref=e111]:
                      - img [ref=e112]
                    - generic [ref=e115]: Rotate selection · Select an editable object first
                  - generic "Scale selection · Select an editable object first" [ref=e116]:
                    - button "Scale selection" [disabled] [ref=e117]:
                      - img [ref=e118]
                    - generic [ref=e123]: Scale selection · Select an editable object first
                - group "Site geometry" [ref=e125]:
                  - generic [ref=e126]: Site
                  - generic "Draw a rectangular site boundary" [ref=e127]:
                    - button "Draw rectangular boundary" [ref=e128]:
                      - img [ref=e129]
                    - generic [ref=e131]: Draw a rectangular site boundary
                  - generic "Draw a closed site boundary" [ref=e132]:
                    - button "Draw site boundary" [ref=e133]:
                      - img [ref=e134]
                    - generic [ref=e136]: Draw a closed site boundary
                  - generic "Edit site boundary · Draw a site boundary first" [ref=e137]:
                    - button "Edit site boundary" [disabled] [ref=e138]:
                      - img [ref=e139]
                    - generic [ref=e142]: Edit site boundary · Draw a site boundary first
                  - generic "Draw a road or infrastructure centerline" [ref=e143]:
                    - button "Draw alignment" [ref=e144]:
                      - img [ref=e145]
                    - generic [ref=e149]: Draw a road or infrastructure centerline
                  - generic "Edit alignment · Draw an alignment first" [ref=e150]:
                    - button "Edit alignment" [disabled] [ref=e151]:
                      - img [ref=e152]
                    - generic [ref=e159]: Edit alignment · Draw an alignment first
                - generic [ref=e161]: View
                - generic "Measure distance, elevation, slope, area or clearance · M" [ref=e162]:
                  - button "Measure" [ref=e163]:
                    - img [ref=e164]
                  - generic [ref=e170]: Measure distance, elevation, slope, area or clearance · M
                - generic "Fit the project in view · F" [ref=e171]:
                  - button "Fit project" [ref=e172]:
                    - img [ref=e173]
                  - generic [ref=e179]: Fit the project in view · F
                - generic [ref=e181]: Actions
                - generic "Duplicate selection · Select an editable object first" [ref=e182]:
                  - button "Duplicate selection" [disabled] [ref=e183]:
                    - img [ref=e184]
                  - generic [ref=e187]: Duplicate selection · Select an editable object first
                - generic "Delete selection · Select an editable object first" [ref=e188]:
                  - button "Delete selection" [disabled] [ref=e189]:
                    - img [ref=e190]
                  - generic [ref=e193]: Delete selection · Select an editable object first
                - generic "Undo · No object edits to undo" [ref=e195]:
                  - button "Undo" [disabled] [ref=e196]:
                    - img [ref=e197]
                  - generic [ref=e200]: Undo · No object edits to undo
                - generic "Redo · No object edits to redo" [ref=e201]:
                  - button "Redo" [disabled] [ref=e202]:
                    - img [ref=e203]
                  - generic [ref=e206]: Redo · No object edits to redo
              - generic [ref=e207]:
                - generic "Scene / Sun study" [ref=e208]:
                  - button "Scene / Sun study" [ref=e209]:
                    - img [ref=e210]
                - button "Search workspace" [ref=e217]:
                  - img [ref=e218]
                - group [ref=e221]:
                  - generic "Import site geometry" [ref=e222] [cursor=pointer]:
                    - img [ref=e223]
                    - text: Import
              - group "Camera orientation gizmo" [ref=e226]:
                - generic [ref=e227]:
                  - img
                  - button "Positive Y axis view" [ref=e228]: +Y
                  - button "Negative Z axis view" [disabled] [ref=e229]: −Z
                  - button "Positive X axis view" [ref=e230]: +X
                  - button "Negative X axis view" [ref=e231]: −X
                  - button "Positive Z axis view" [ref=e232]: +Z
                  - button "Negative Y axis view" [ref=e233]: −Y
            - complementary [ref=e235]:
              - generic [ref=e237]:
                - generic [ref=e238]:
                  - generic [ref=e240]:
                    - generic [ref=e241]: Analysis
                    - button "Close inspector" [ref=e242]:
                      - img [ref=e243]
                  - tabpanel "Analysis" [ref=e246]:
                    - region "Guided Analysis" [ref=e247]:
                      - generic [ref=e248]:
                        - generic [ref=e249]:
                          - heading "Guided workflow" [level=2] [ref=e250]
                          - button "Advanced mode" [ref=e251]
                        - generic "Current analysis context" [ref=e252]:
                          - paragraph [ref=e253]: Foundations and soil · Bounded foundation study · Step 1 of 4
                          - paragraph [ref=e254]: "Selected: No components selected · 56 CAD components"
                          - paragraph [ref=e255]: "Active result: None current · revision 125"
                          - paragraph [ref=e256]: "Next: Choose an analysis type"
                          - link "Diagnostics for this saved model" [ref=e257] [cursor=pointer]:
                            - /url: /diagnostics?project_id=805&model_revision_id=125
                          - button "Refresh saved analysis" [ref=e258]
                          - button "Restore model" [ref=e259]
                        - navigation "Analysis steps" [ref=e260]:
                          - button "1 SELECT" [ref=e261]
                          - button "2 INPUTS" [ref=e262]
                          - button "3 ANALYZE" [ref=e263]
                          - button "4 RESULTS" [ref=e264]
                      - heading "Choose what to analyze" [level=3] [ref=e265]
                      - generic [ref=e266]:
                        - button "Structural analysis Missing inputs · Select two columns and a beam for backend geometry inspection; declare materials, loads and joints." [ref=e267]:
                          - text: Structural analysis
                          - generic [ref=e268]: Missing inputs · Select two columns and a beam for backend geometry inspection; declare materials, loads and joints.
                        - button "Slabs and floor systems Missing inputs · Explicit slab/support mapping, pressure, declarations and supporting frame inputs are required; no shell behavior is inferred." [ref=e269]:
                          - text: Slabs and floor systems
                          - generic [ref=e270]: Missing inputs · Explicit slab/support mapping, pressure, declarations and supporting frame inputs are required; no shell behavior is inferred.
                        - button "Foundations and soil Supported · Saved bounded foundation inputs and source binding validated; unsupported checks remain disabled." [pressed] [ref=e271]:
                          - text: Foundations and soil
                          - generic [ref=e272]: Supported · Saved bounded foundation inputs and source binding validated; unsupported checks remain disabled.
                      - button "Continue to inputs" [ref=e273]
                      - generic [ref=e274]:
                        - button "Reload saved inputs and results" [ref=e275]
                        - paragraph [ref=e276]: Reopening restores browser view preferences and saved evidence only. It never authorizes or reruns a solver.
                - tablist "Inspector views" [ref=e277]:
                  - tab "Layers" [ref=e278]:
                    - img [ref=e279]
                    - generic [ref=e283]: Layers
                  - tab "Inspect" [ref=e284]:
                    - img [ref=e285]
                    - generic [ref=e287]: Inspect
                  - tab "History" [ref=e288]:
                    - img [ref=e289]
                    - generic [ref=e293]: History
                  - tab "Analysis" [selected] [ref=e294]:
                    - img [ref=e295]
                    - generic [ref=e298]: Analysis
                  - tab "Review" [ref=e299]:
                    - img [ref=e300]
                    - generic [ref=e303]: Review
        - region "Engineering dock" [ref=e304]:
          - generic [ref=e306]:
            - button "Engineering dock" [ref=e307]:
              - generic [ref=e308]: Engineering dock
              - img [ref=e309]
            - button "Cost —" [ref=e312]:
              - 'generic "Cost: —" [ref=e313]':
                - img [ref=e314]
                - generic [ref=e316]: Cost
                - generic [ref=e317]: —
            - button "Cement —" [ref=e319]:
              - 'generic "Cement: —" [ref=e320]':
                - img [ref=e321]
                - generic [ref=e324]: Cement
                - generic [ref=e325]: —
            - button "Steel —" [ref=e327]:
              - 'generic "Steel: —" [ref=e328]':
                - img [ref=e329]
                - generic [ref=e333]: Steel
                - generic [ref=e334]: —
            - button "Excavation —" [ref=e336]:
              - 'generic "Excavation: —" [ref=e337]':
                - img [ref=e338]
                - generic [ref=e342]: Excavation
                - generic [ref=e343]: —
            - button "Duration —" [ref=e345]:
              - 'generic "Duration: —" [ref=e346]':
                - img [ref=e347]
                - generic [ref=e350]: Duration
                - generic [ref=e351]: —
            - button "Area —" [ref=e353]:
              - 'generic "Area: —" [ref=e354]':
                - img [ref=e355]
                - generic [ref=e358]: Area
                - generic [ref=e359]: —
            - button "Risk —" [ref=e361]:
              - 'generic "Risk: —" [ref=e362]':
                - img [ref=e363]
                - generic [ref=e366]: Risk
                - generic [ref=e367]: —
  - alert [ref=e368]
  - complementary "GeoAI Assistant" [ref=e369]:
    - separator "Resize assistant" [ref=e370]
    - generic [ref=e371]:
      - generic [ref=e372]:
        - img [ref=e373]
        - heading "GeoAI Assistant" [level=2] [ref=e376]
      - generic [ref=e377]:
        - button "Compact assistant" [ref=e378] [cursor=pointer]:
          - img [ref=e379]
        - button "Close site assistant" [ref=e384] [cursor=pointer]:
          - img [ref=e385]
    - status [ref=e388]:
      - strong [ref=e390]: Connection error
    - alert [ref=e391]:
      - paragraph [ref=e392]: Nebius connection failed. Retry manually.
      - button "Refresh availability" [ref=e393] [cursor=pointer]
    - generic "Assistant task history" [ref=e394]:
      - article [ref=e395]:
        - generic [ref=e396]:
          - generic [ref=e397]: You
          - paragraph [ref=e398]: Where are my saved results?
        - generic [ref=e399]:
          - generic [ref=e400]: GeoAI
          - generic [ref=e401]:
            - paragraph [ref=e402]:
              - text: You can inspect
              - strong [ref=e403]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e404]:
              - listitem [ref=e405]:
                - text: Open
                - strong [ref=e406]: Analyze / Results
                - text: .
              - listitem [ref=e407]: Select a saved evidence record.
              - listitem [ref=e408]: Check whether the source is current.
            - paragraph [ref=e409]:
              - link "Open diagnostics" [ref=e410] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e411]:
              - text: Opening a result does
              - strong [ref=e412]: not
              - text: run a solver or save a model.
          - group [ref=e413]:
            - generic "Message details" [ref=e414] [cursor=pointer]
      - article [ref=e415]:
        - generic [ref=e416]:
          - generic [ref=e417]: You
          - paragraph [ref=e418]: Show existing saved results
        - generic [ref=e419]:
          - generic [ref=e420]: GeoAI
          - generic [ref=e421]:
            - paragraph [ref=e422]:
              - text: You can inspect
              - strong [ref=e423]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e424]:
              - listitem [ref=e425]:
                - text: Open
                - strong [ref=e426]: Analyze / Results
                - text: .
              - listitem [ref=e427]: Select a saved evidence record.
              - listitem [ref=e428]: Check whether the source is current.
            - paragraph [ref=e429]:
              - link "Open diagnostics" [ref=e430] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e431]:
              - text: Opening a result does
              - strong [ref=e432]: not
              - text: run a solver or save a model.
          - generic [ref=e433]:
            - paragraph [ref=e434]: Checked saved project evidence
            - group [ref=e435]:
              - generic "Evidence" [ref=e436] [cursor=pointer]
          - generic [ref=e437]:
            - paragraph [ref=e438]: Ready to open results
            - button "Open results" [ref=e439] [cursor=pointer]
            - group [ref=e440]:
              - generic "Evidence" [ref=e441] [cursor=pointer]
          - group [ref=e442]:
            - generic "Message details" [ref=e443] [cursor=pointer]
      - article [ref=e444]:
        - generic [ref=e445]:
          - generic [ref=e446]: You
          - paragraph [ref=e447]: Recorded question 0
        - generic [ref=e448]:
          - generic [ref=e449]: GeoAI
          - generic [ref=e450]:
            - paragraph [ref=e451]:
              - text: You can inspect
              - strong [ref=e452]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e453]:
              - listitem [ref=e454]:
                - text: Open
                - strong [ref=e455]: Analyze / Results
                - text: .
              - listitem [ref=e456]: Select a saved evidence record.
              - listitem [ref=e457]: Check whether the source is current.
            - paragraph [ref=e458]:
              - link "Open diagnostics" [ref=e459] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e460]:
              - text: Opening a result does
              - strong [ref=e461]: not
              - text: run a solver or save a model.
          - group [ref=e462]:
            - generic "Message details" [ref=e463] [cursor=pointer]
      - article [ref=e464]:
        - generic [ref=e465]:
          - generic [ref=e466]: You
          - paragraph [ref=e467]: Recorded question 1
        - generic [ref=e468]:
          - generic [ref=e469]: GeoAI
          - generic [ref=e470]:
            - paragraph [ref=e471]:
              - text: You can inspect
              - strong [ref=e472]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e473]:
              - listitem [ref=e474]:
                - text: Open
                - strong [ref=e475]: Analyze / Results
                - text: .
              - listitem [ref=e476]: Select a saved evidence record.
              - listitem [ref=e477]: Check whether the source is current.
            - paragraph [ref=e478]:
              - link "Open diagnostics" [ref=e479] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e480]:
              - text: Opening a result does
              - strong [ref=e481]: not
              - text: run a solver or save a model.
          - group [ref=e482]:
            - generic "Message details" [ref=e483] [cursor=pointer]
      - article [ref=e484]:
        - generic [ref=e485]:
          - generic [ref=e486]: You
          - paragraph [ref=e487]: Recorded question 2
        - generic [ref=e488]:
          - generic [ref=e489]: GeoAI
          - generic [ref=e490]:
            - paragraph [ref=e491]:
              - text: You can inspect
              - strong [ref=e492]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e493]:
              - listitem [ref=e494]:
                - text: Open
                - strong [ref=e495]: Analyze / Results
                - text: .
              - listitem [ref=e496]: Select a saved evidence record.
              - listitem [ref=e497]: Check whether the source is current.
            - paragraph [ref=e498]:
              - link "Open diagnostics" [ref=e499] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e500]:
              - text: Opening a result does
              - strong [ref=e501]: not
              - text: run a solver or save a model.
          - group [ref=e502]:
            - generic "Message details" [ref=e503] [cursor=pointer]
      - article [ref=e504]:
        - generic [ref=e505]:
          - generic [ref=e506]: You
          - paragraph [ref=e507]: Recorded question 3
        - generic [ref=e508]:
          - generic [ref=e509]: GeoAI
          - generic [ref=e510]:
            - paragraph [ref=e511]:
              - text: You can inspect
              - strong [ref=e512]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e513]:
              - listitem [ref=e514]:
                - text: Open
                - strong [ref=e515]: Analyze / Results
                - text: .
              - listitem [ref=e516]: Select a saved evidence record.
              - listitem [ref=e517]: Check whether the source is current.
            - paragraph [ref=e518]:
              - link "Open diagnostics" [ref=e519] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e520]:
              - text: Opening a result does
              - strong [ref=e521]: not
              - text: run a solver or save a model.
          - group [ref=e522]:
            - generic "Message details" [ref=e523] [cursor=pointer]
      - article [ref=e524]:
        - generic [ref=e525]:
          - generic [ref=e526]: You
          - paragraph [ref=e527]: Recorded question 4
        - generic [ref=e528]:
          - generic [ref=e529]: GeoAI
          - generic [ref=e530]:
            - paragraph [ref=e531]:
              - text: You can inspect
              - strong [ref=e532]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e533]:
              - listitem [ref=e534]:
                - text: Open
                - strong [ref=e535]: Analyze / Results
                - text: .
              - listitem [ref=e536]: Select a saved evidence record.
              - listitem [ref=e537]: Check whether the source is current.
            - paragraph [ref=e538]:
              - link "Open diagnostics" [ref=e539] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e540]:
              - text: Opening a result does
              - strong [ref=e541]: not
              - text: run a solver or save a model.
          - group [ref=e542]:
            - generic "Message details" [ref=e543] [cursor=pointer]
      - article [ref=e544]:
        - generic [ref=e545]:
          - generic [ref=e546]: You
          - paragraph [ref=e547]: Recorded question 5
        - generic [ref=e548]:
          - generic [ref=e549]: GeoAI
          - generic [ref=e550]:
            - paragraph [ref=e551]:
              - text: You can inspect
              - strong [ref=e552]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e553]:
              - listitem [ref=e554]:
                - text: Open
                - strong [ref=e555]: Analyze / Results
                - text: .
              - listitem [ref=e556]: Select a saved evidence record.
              - listitem [ref=e557]: Check whether the source is current.
            - paragraph [ref=e558]:
              - link "Open diagnostics" [ref=e559] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e560]:
              - text: Opening a result does
              - strong [ref=e561]: not
              - text: run a solver or save a model.
          - group [ref=e562]:
            - generic "Message details" [ref=e563] [cursor=pointer]
      - article [ref=e564]:
        - generic [ref=e565]:
          - generic [ref=e566]: You
          - paragraph [ref=e567]: Recorded question 6
        - generic [ref=e568]:
          - generic [ref=e569]: GeoAI
          - generic [ref=e570]:
            - paragraph [ref=e571]:
              - text: You can inspect
              - strong [ref=e572]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e573]:
              - listitem [ref=e574]:
                - text: Open
                - strong [ref=e575]: Analyze / Results
                - text: .
              - listitem [ref=e576]: Select a saved evidence record.
              - listitem [ref=e577]: Check whether the source is current.
            - paragraph [ref=e578]:
              - link "Open diagnostics" [ref=e579] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e580]:
              - text: Opening a result does
              - strong [ref=e581]: not
              - text: run a solver or save a model.
          - group [ref=e582]:
            - generic "Message details" [ref=e583] [cursor=pointer]
      - article [ref=e584]:
        - generic [ref=e585]:
          - generic [ref=e586]: You
          - paragraph [ref=e587]: Recorded question 7
        - generic [ref=e588]:
          - generic [ref=e589]: GeoAI
          - generic [ref=e590]:
            - paragraph [ref=e591]:
              - text: You can inspect
              - strong [ref=e592]: saved analysis results
              - text: without starting a calculation.
            - list [ref=e593]:
              - listitem [ref=e594]:
                - text: Open
                - strong [ref=e595]: Analyze / Results
                - text: .
              - listitem [ref=e596]: Select a saved evidence record.
              - listitem [ref=e597]: Check whether the source is current.
            - paragraph [ref=e598]:
              - link "Open diagnostics" [ref=e599] [cursor=pointer]:
                - /url: /diagnostics
              - text: for existing service information.
            - paragraph [ref=e600]:
              - text: Opening a result does
              - strong [ref=e601]: not
              - text: run a solver or save a model.
          - group [ref=e602]:
            - generic "Message details" [ref=e603] [cursor=pointer]
      - article [ref=e604]:
        - generic [ref=e605]:
          - generic [ref=e606]: You
          - paragraph [ref=e607]: Manual service failure fixture
        - generic [ref=e609]: GeoAI
    - button "Retry" [ref=e610] [cursor=pointer]
    - group [ref=e611]:
      - generic "Details" [ref=e612] [cursor=pointer]
      - option "GLM-5.3-Flash" [selected]
    - generic [ref=e613]:
      - generic [ref=e614]: Message GeoAI Assistant
      - textbox "Message GeoAI Assistant" [ref=e615]:
        - /placeholder: Ask GeoAI…
        - text: Manual service failure fixture
      - generic [ref=e616]:
        - generic [ref=e617]: Changes need your review
        - button "Send" [ref=e618] [cursor=pointer]:
          - img [ref=e619]
          - text: Send
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | const model="zai-org/GLM-5.3-Flash";
  3  | const reply="You can inspect **saved analysis results** without starting a calculation.\n\n1. Open **Analyze / Results**.\n2. Select a saved evidence record.\n3. Check whether the source is current.\n\n[Open diagnostics](/diagnostics) for existing service information.\n\nOpening a result does **not** run a solver or save a model.";
  4  | const oldTask={id:"sanitized-ui-history",request:{message:"Where are my saved results?",project_id:805,revision_id:null,selected_ids:[],dirty:false,page:"/projects/805/workspace",model},status:"SUCCEEDED",reply,events:[{type:"delta",text:reply}],model};
  5  | for(const width of [1280,1600]) test(`conversation, actions and blocked states ${width}`,async({page})=>{
  6  |  await page.setViewportSize({width,height:900});
  7  |  let sends=0,mode="success"; let history:unknown[]=[oldTask]; const writes:string[]=[],errors:string[]=[];
  8  |  page.on('pageerror',e=>errors.push(e.message));
  9  |  await page.route('**/*',async route=>{
  10 |   const r=route.request(),u=new URL(r.url());
  11 |   if(!['localhost','127.0.0.1'].includes(u.hostname))return route.abort();
  12 |   if(u.pathname.endsWith('/api/geocode/map-runtime-config'))return route.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}});
  13 |   if(u.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock availability. No provider request.',models:[model],requestAllowance:3,usage:{daily_requests:0,accounted_daily_tokens:14487,accounted_usd:.0024219},dailyTokenAllowance:200000}});
  14 |   if(u.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:history}});
  15 |   if(u.pathname.endsWith('/api/assistant/turn')){
  16 |    sends++; const p=r.postDataJSON();expect(p.model).toBe(model);
  17 |    if(mode==='quota')return route.fulfill({status:429,json:{detail:{code:'DAILY_REQUEST_LIMIT',availability:'RATE_LIMITED',message:'Assistant daily request limit reached.'}}});
  18 |    if(mode==='failure')return route.fulfill({status:503,json:{detail:{code:'PROVIDER_FAILURE',availability:'DISABLED',message:'Nebius connection failed. Retry manually.'}}});
  19 |    const events=[{type:'progress',text:'Reading saved context and checking selected Nebius model availability'},{type:'tool_start',name:'read_context'},{type:'delta',text:reply},{type:'tool_result',name:'read_context',ok:true,result:{kind:'context',notice:'Sanitized recorded event shape; automated fixture.'}},{type:'tool_result',name:'navigate',ok:true,result:{kind:'navigation',projectId:805,href:'/projects/805/workspace',destination:'results'}}];
  20 |    const task={...oldTask,id:p.request_id,request:p,events};history=[...history,task];
  21 |    return route.fulfill({contentType:'text/event-stream',body:[...events,{type:'task',task}].map(e=>'data: '+JSON.stringify(e)+'\n\n').join('')});
  22 |   }
  23 |   if(!['GET','HEAD','OPTIONS'].includes(r.method())){writes.push(r.method()+' '+u.pathname);return route.abort();}
  24 |   return route.continue();
  25 |  });
  26 |  await page.goto('/projects/805/workspace');
  27 |  await expect(page.locator('.cesium-widget canvas')).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  28 |  await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();
  29 |  const panel=page.getByRole('complementary',{name:'GeoAI Assistant'}),pane=panel.getByLabel('Assistant task history');
  30 |  await expect(panel.getByText('saved analysis results',{exact:true})).toBeVisible();
  31 |  await expect(panel.locator('strong').filter({hasText:'saved analysis results'})).toHaveCount(1);
  32 |  await expect(panel.getByRole('link',{name:'Open diagnostics'})).toHaveAttribute('href','/diagnostics');
  33 |  await expect(panel.getByLabel('Assistant model')).not.toBeVisible();
  34 |  await page.screenshot({path:`../docs/assistant-ui/after-${width}.png`});
  35 |  await panel.getByRole('button',{name:'Expand assistant'}).click();
  36 |  const separator=panel.getByRole('separator',{name:'Resize assistant'});await separator.focus();await page.keyboard.press('ArrowLeft');
  37 |  await expect(separator).toHaveAttribute('aria-valuenow','664');
  38 |  const box=await panel.boundingBox();expect(box!.width).toBeLessThanOrEqual(width/2+1);expect(width-box!.width).toBeGreaterThanOrEqual(width/2-1);
  39 |  await page.screenshot({path:`../docs/assistant-ui/expanded-${width}.png`});
  40 |  await panel.getByRole('textbox').fill('Show existing saved results');
  41 |  await panel.getByRole('button',{name:'Send',exact:true}).click();
  42 |  await expect(panel.getByText('Checked saved project evidence',{exact:true})).toBeVisible();
  43 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Completed');
  44 |  await panel.getByRole('button',{name:'Open results',exact:true}).click();
  45 |  await expect(panel.locator('.assistant-action-status')).toContainText('Opened');
  46 |  await expect(panel.locator('.assistant-action-status')).toContainText('No calculation was started or model saved');
  47 |  await page.screenshot({path:`../docs/assistant-ui/action-${width}.png`});
  48 |  // History grows through explicit manual refresh; it never sends an inference request.
  49 |  history=[...history,...Array.from({length:8},(_,i)=>({...oldTask,id:'older-'+i,request:{...oldTask.request,message:'Recorded question '+i}}))];
  50 |  await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();
  51 |  await expect(panel.locator('article')).toHaveCount(10);
  52 |  await panel.getByText('Details',{exact:true}).click();
  53 |  await pane.evaluate(el=>{el.scrollTop=0;el.dispatchEvent(new Event('scroll'));});
  54 |  const top=await pane.evaluate(el=>el.scrollTop);expect(top).toBe(0);
  55 |  await panel.getByText('Details',{exact:true}).click();await panel.getByRole('button',{name:'Refresh history'}).click();await panel.getByText('Details',{exact:true}).click();
  56 |  expect(await pane.evaluate(el=>el.scrollTop)).toBeLessThan(10);
  57 |  await panel.getByRole('button',{name:'New message ↓'}).click();
  58 |  expect(await pane.evaluate(el=>el.scrollHeight-el.clientHeight-el.scrollTop)).toBeLessThan(65);
  59 |  mode='quota';await panel.getByRole('textbox').fill('A blocked request');await panel.getByRole('button',{name:'Send',exact:true}).click();
  60 |  await expect(panel.getByRole('alert')).toContainText('approved live test has used all 3 turns');
  61 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Usage limit reached');
  62 |  await expect(panel.getByRole('alert')).toContainText('not a token or money limit');
  63 |  await page.screenshot({path:`../docs/assistant-ui/quota-${width}.png`});
  64 |  expect(sends).toBe(2);await page.waitForTimeout(300);expect(sends).toBe(2);
  65 |  mode='failure';await panel.getByRole('textbox').fill('Manual service failure fixture');await panel.getByRole('button',{name:'Send',exact:true}).click();
  66 |  await expect(panel.getByLabel('Assistant availability')).toHaveText('Connection error');await expect(panel.getByRole('alert')).toContainText('Nebius connection failed');
  67 |  await page.screenshot({path:`../docs/assistant-ui/failure-${width}.png`});expect(sends).toBe(3);
> 68 |  await page.keyboard.press('Escape');await expect(panel).toHaveCount(0);
     |                                                          ^ Error: expect(locator).toHaveCount(expected) failed
  69 |  expect(writes).toEqual([]);expect(errors).toEqual([]);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  70 | });
  71 | for(const width of [1280,1600]) test(`loading and manual cancellation ${width}`,async({page})=>{
  72 |  await page.setViewportSize({width,height:900});let sends=0,release!:()=>void;const gate=new Promise<void>(r=>release=r);
  73 |  await page.route('**/*',async route=>{const req=route.request(),url=new URL(req.url());if(!['localhost','127.0.0.1'].includes(url.hostname))return route.abort();
  74 |   if(url.pathname.endsWith('/api/assistant/history'))return route.fulfill({json:{tasks:[]}});
  75 |   if(url.pathname.endsWith('/api/assistant/status'))return route.fulfill({json:{enabled:true,state:'AVAILABLE',message:'Mock only',models:[model]}});
  76 |   if(url.pathname.endsWith('/api/assistant/turn')){sends++;await gate;return route.abort().catch(()=>{});}
  77 |   if(!['GET','HEAD','OPTIONS'].includes(req.method()))return route.abort();return route.continue();});
  78 |  await page.goto('/projects/805/workspace');await page.getByRole('button',{name:'GeoAI Assistant',exact:true}).click();const panel=page.getByRole('complementary',{name:'GeoAI Assistant'});
  79 |  await panel.getByRole('textbox').fill('Explain this project');await panel.getByRole('button',{name:'Send',exact:true}).click();await expect(panel.getByLabel('Assistant availability')).toHaveText('Thinking');
  80 |  await page.screenshot({path:`../docs/assistant-ui/thinking-${width}.png`});await panel.getByRole('button',{name:'Stop response'}).click();release();
  81 |  await expect(panel.getByRole('alert')).toContainText('Usage may be unknown');await expect(panel.getByRole('textbox')).toHaveValue('Explain this project');await expect(panel.getByLabel('Assistant availability')).toHaveText('Ready');
  82 |  await page.screenshot({path:`../docs/assistant-ui/stopped-${width}.png`});await page.waitForTimeout(250);expect(sends).toBe(1);
  83 | });
  84 | 
```