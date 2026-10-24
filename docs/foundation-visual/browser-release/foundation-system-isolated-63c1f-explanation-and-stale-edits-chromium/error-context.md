# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: foundation-system.spec.ts >> isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits
- Location: e2e\foundation-system.spec.ts:5:5

# Error details

```
TimeoutError: page.waitForResponse: Timeout 30000ms exceeded while waiting for event "response"
```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to main content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e4]:
    - banner [ref=e5]:
      - link "GeoAI home" [ref=e6] [cursor=pointer]:
        - /url: /
        - generic "GeoAI" [ref=e7]
      - heading "RC footing nominal flexure — synthetic review" [level=1] [ref=e13]
      - generic [ref=e14]:
        - link "3D Sandbox editor" [ref=e15] [cursor=pointer]:
          - /url: /projects/999999/workspace?local=1
        - link "Projects" [ref=e19] [cursor=pointer]:
          - /url: /dashboard
        - generic [ref=e20]:
          - button "Save site geometry" [ref=e21]
          - link [ref=e26] [cursor=pointer]:
            - /url: /projects/804/report
            - button "Export" [ref=e27]
        - link [ref=e31] [cursor=pointer]:
          - /url: /projects/new
          - button "New concept" [ref=e32]
        - link "Open settings" [ref=e34] [cursor=pointer]:
          - /url: /settings
    - main [ref=e38]:
      - generic [ref=e41]:
        - generic [ref=e42]:
          - generic "Design workflow" [ref=e46]:
            - button "1 Site" [ref=e47]
            - group [ref=e48]:
              - generic "Workflow help" [ref=e49] [cursor=pointer]
            - group [ref=e50]:
              - generic "2 Create / Import" [ref=e51] [cursor=pointer]
            - button "3 Review 3D" [ref=e52]
            - button "4 Edit" [ref=e53]
            - button "5 Analyze / Results" [ref=e54]
            - button "6 Review" [ref=e55]
            - status [ref=e56]: Saved · v1
            - button "Save model" [disabled]
          - generic [ref=e57]:
            - generic [ref=e58]:
              - generic [ref=e61]:
                - generic: 12.97160° N · 77.59460° E
                - generic [ref=e62]:
                  - generic "Mouse navigation" [ref=e63]:
                    - button "Select" [pressed] [ref=e64]
                    - button "Orbit" [ref=e65]
                    - button "Pan" [ref=e66]
                    - button "Mouse controls" [ref=e67]
                  - generic "Viewport presentation" [ref=e68]:
                    - generic [ref=e69]:
                      - button "Model view" [pressed] [ref=e70]
                      - generic [ref=e71]: /
                      - button "Site view" [ref=e72]
                      - generic [ref=e73]: Illustrative finishes · not material evidence
                    - generic [ref=e74]:
                      - group [ref=e75]:
                        - generic "Standard views" [ref=e76] [cursor=pointer]
                      - button "Focus Structure" [ref=e77]
                      - button "Fit All" [ref=e78]
                      - button "Fit selection" [disabled] [ref=e79]
                      - button "Dimensions off" [ref=e80]
                      - group [ref=e81]:
                        - generic "Display legend" [ref=e82] [cursor=pointer]
                  - generic [ref=e84]:
                    - generic "3D workspace viewport" [ref=e87]
                    - button "Full screen" [ref=e89] [cursor=pointer]
              - complementary "Workspace tools" [ref=e93]:
                - group "Object editing" [ref=e94]:
                  - generic [ref=e95]: Edit
                  - generic "Click to select and inspect · Ctrl to add · V" [ref=e96]:
                    - button "Select object" [pressed] [ref=e97]
                  - generic "Move selection · Select an editable object first" [ref=e101]:
                    - button "Move selection" [disabled] [ref=e102]
                  - generic "Rotate selection · Select an editable object first" [ref=e109]:
                    - button "Rotate selection" [disabled] [ref=e110]
                  - generic "Scale selection · Select an editable object first" [ref=e115]:
                    - button "Scale selection" [disabled] [ref=e116]
                - group "Site geometry" [ref=e124]:
                  - generic [ref=e125]: Site
                  - generic "Draw a rectangular site boundary" [ref=e126]:
                    - button "Draw rectangular boundary" [ref=e127]
                  - generic "Draw a closed site boundary" [ref=e131]:
                    - button "Draw site boundary" [ref=e132]
                  - generic "Drag existing boundary vertices" [ref=e136]:
                    - button "Edit site boundary" [ref=e137]
                  - generic "Draw a road or infrastructure centerline" [ref=e142]:
                    - button "Draw alignment" [ref=e143]
                  - generic "Edit alignment · Draw an alignment first" [ref=e149]:
                    - button "Edit alignment" [disabled] [ref=e150]
                - generic [ref=e160]: View
                - generic "Measure distance, elevation, slope, area or clearance · M" [ref=e161]:
                  - button "Measure" [ref=e162]
                - generic "Fit the project in view · F" [ref=e170]:
                  - button "Fit project" [ref=e171]
                - generic [ref=e180]: Actions
                - generic "Duplicate selection · Select an editable object first" [ref=e181]:
                  - button "Duplicate selection" [disabled] [ref=e182]
                - generic "Delete selection · Select an editable object first" [ref=e187]:
                  - button "Delete selection" [disabled] [ref=e188]
                - generic "Undo · No object edits to undo" [ref=e194]:
                  - button "Undo" [disabled] [ref=e195]
                - generic "Redo · No object edits to redo" [ref=e200]:
                  - button "Redo" [disabled] [ref=e201]
              - generic [ref=e206]:
                - generic "Scene / Sun study" [ref=e207]:
                  - button "Scene / Sun study" [ref=e208]
                - button "Search workspace" [ref=e216]
                - group [ref=e220]:
                  - generic "Import site geometry" [ref=e221] [cursor=pointer]: Import
              - button "Show AI Copilot panel" [ref=e226]:
                - generic [ref=e230]: Assistant
              - group "Camera orientation gizmo" [ref=e231]:
                - button "Positive Y axis view" [ref=e238]: "Y"
                - button "Negative Z axis view" [disabled] [ref=e239]
                - button "Positive X axis view" [ref=e240]: X
                - button "Negative X axis view" [ref=e241]
                - button "Positive Z axis view" [ref=e242]: Z
                - button "Negative Y axis view" [ref=e243]
            - complementary [ref=e245]:
              - generic [ref=e247]:
                - generic [ref=e248]:
                  - generic [ref=e250]:
                    - generic [ref=e251]: Analysis
                    - button "Close inspector" [ref=e252]
                  - tabpanel "Analysis" [ref=e256]:
                    - generic [ref=e257]:
                      - region "Analysis overview" [ref=e258]:
                        - generic [ref=e259]:
                          - heading "Analysis" [level=2] [ref=e260]
                          - paragraph [ref=e261]: Saved structural model
                        - generic [ref=e262]:
                          - paragraph [ref=e263]: Geometry only
                          - paragraph [ref=e264]: The drawing defines model geometry. It does not establish structural sections, loads or material properties.
                        - button "Inspect drawing sources" [ref=e265]
                        - paragraph [ref=e266]: Numerical verification is not structural design approval.
                      - region "Integrated foundation workflow" [ref=e267]:
                        - heading "Foundation engineering" [level=3] [ref=e268]
                        - paragraph [ref=e269]: Synthetic review · saved CAD identities · no engineering approval
                        - button "Create separate foundation study from 804" [disabled] [ref=e270]
                      - group [ref=e271]:
                        - generic "Advanced analysis · inputs, tools and evidence" [ref=e272] [cursor=pointer]
                        - option "UNSELECTED" [selected]
                        - option "INDIA"
                        - option "UNITED_STATES"
                        - option "NONE" [selected]
                        - option "IS456"
                        - option "ACI318"
                        - option "Explicitly select reviewed identity" [selected]
                        - option "CAD footing SW"
                        - option "CAD footing SE"
                        - option "CAD footing NW"
                        - option "CAD footing NE"
                        - option "Explicitly select reviewed identity" [selected]
                        - option "CAD footing SW"
                        - option "CAD footing SE"
                        - option "CAD footing NW"
                        - option "CAD footing NE"
                        - option "Explicitly select reviewed identity" [selected]
                        - option "CAD footing SW"
                        - option "CAD footing SE"
                        - option "CAD footing NW"
                        - option "CAD footing NE"
                        - option "Explicitly select reviewed identity" [selected]
                        - option "CAD footing SW"
                        - option "CAD footing SE"
                        - option "CAD footing NW"
                        - option "CAD footing NE"
                        - option "Missing/unreviewed — keep BLOCKED" [selected]
                        - option "CAD footing SW · drawing-cad:614f117ae2a74794:9A"
                        - option "UNVERIFIED" [selected]
                        - option "MEASURED"
                        - option "MANUFACTURER_DATA"
                        - option "ENGINEER_DECLARED"
                        - option "SYNTHETIC_VERIFICATION"
                        - option "Missing/unreviewed — keep BLOCKED" [selected]
                        - option "CAD footing SE · drawing-cad:614f117ae2a74794:AC"
                        - option "UNVERIFIED" [selected]
                        - option "MEASURED"
                        - option "MANUFACTURER_DATA"
                        - option "ENGINEER_DECLARED"
                        - option "SYNTHETIC_VERIFICATION"
                        - option "Missing/unreviewed — keep BLOCKED" [selected]
                        - option "CAD footing NW · drawing-cad:614f117ae2a74794:A3"
                        - option "UNVERIFIED" [selected]
                        - option "MEASURED"
                        - option "MANUFACTURER_DATA"
                        - option "ENGINEER_DECLARED"
                        - option "SYNTHETIC_VERIFICATION"
                        - option "Missing/unreviewed — keep BLOCKED" [selected]
                        - option "CAD footing NE · drawing-cad:614f117ae2a74794:B5"
                        - option "UNVERIFIED" [selected]
                        - option "MEASURED"
                        - option "MANUFACTURER_DATA"
                        - option "ENGINEER_DECLARED"
                        - option "SYNTHETIC_VERIFICATION"
                        - option "Select saved component explicitly" [selected]
                        - option "platform-deck · industrial-platform-5x3:platform-deck"
                        - option "CAD slab · drawing-cad:614f117ae2a74794:95"
                        - option "Select saved component explicitly" [selected]
                        - option "beam-east · industrial-platform-5x3:beam-east"
                        - option "beam-north · industrial-platform-5x3:beam-north"
                        - option "beam-south · industrial-platform-5x3:beam-south"
                        - option "beam-west · industrial-platform-5x3:beam-west"
                        - option "CAD beam South · drawing-cad:614f117ae2a74794:96"
                        - option "CAD beam North · drawing-cad:614f117ae2a74794:97"
                        - option "Select saved component explicitly" [selected]
                        - option "beam-east · industrial-platform-5x3:beam-east"
                        - option "beam-north · industrial-platform-5x3:beam-north"
                        - option "beam-south · industrial-platform-5x3:beam-south"
                        - option "beam-west · industrial-platform-5x3:beam-west"
                        - option "CAD beam South · drawing-cad:614f117ae2a74794:96"
                        - option "CAD beam North · drawing-cad:614f117ae2a74794:97"
                        - option "Declare explicitly" [selected]
                        - option "Negative local Up"
                        - option "Declare explicitly" [selected]
                        - option "Symmetric one-way tributary area"
                        - option "Select source entity" [selected]
                        - option "SLAB · LWPOLYLINE · 95"
                        - option "BEAMS · LWPOLYLINE · 96"
                        - option "BEAMS · LWPOLYLINE · 97"
                        - option "BEAMS · LWPOLYLINE · 98"
                        - option "BEAMS · LWPOLYLINE · 99"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · 9A"
                        - option "BASE_PLATES · LWPOLYLINE · 9B · BLOCKED"
                        - option "COLUMNS · LWPOLYLINE · 9C"
                        - option "ANCHORS_DECLARED · CIRCLE · 9D · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · 9E · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · 9F · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · A0 · BLOCKED"
                        - option "CENTRELINES · LINE · A1 · BLOCKED"
                        - option "CENTRELINES · LINE · A2 · BLOCKED"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · A3"
                        - option "BASE_PLATES · LWPOLYLINE · A4 · BLOCKED"
                        - option "COLUMNS · LWPOLYLINE · A5"
                        - option "ANCHORS_DECLARED · CIRCLE · A6 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · A7 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · A8 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · A9 · BLOCKED"
                        - option "CENTRELINES · LINE · AA · BLOCKED"
                        - option "CENTRELINES · LINE · AB · BLOCKED"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · AC"
                        - option "BASE_PLATES · LWPOLYLINE · AD · BLOCKED"
                        - option "COLUMNS · LWPOLYLINE · AE"
                        - option "ANCHORS_DECLARED · CIRCLE · AF · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · B0 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · B1 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · B2 · BLOCKED"
                        - option "CENTRELINES · LINE · B3 · BLOCKED"
                        - option "CENTRELINES · LINE · B4 · BLOCKED"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · B5"
                        - option "BASE_PLATES · LWPOLYLINE · B6 · BLOCKED"
                        - option "COLUMNS · LWPOLYLINE · B7"
                        - option "ANCHORS_DECLARED · CIRCLE · B8 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · B9 · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · BA · BLOCKED"
                        - option "ANCHORS_DECLARED · CIRCLE · BB · BLOCKED"
                        - option "CENTRELINES · LINE · BC · BLOCKED"
                        - option "CENTRELINES · LINE · BD · BLOCKED"
                        - option "STAIR_CONCEPT · LWPOLYLINE · BE · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · BF · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C0 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C1 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C2 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C3 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C4 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C5 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C6 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C7 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C8 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · C9 · BLOCKED"
                        - option "STAIR_CONCEPT · LINE · CA · BLOCKED"
                        - option "WARNINGS · TEXT · CB · BLOCKED"
                        - option "DIMENSIONS · LINE · CC · BLOCKED"
                        - option "DIMENSIONS · LINE · CD · BLOCKED"
                        - option "DIMENSIONS · LINE · CE · BLOCKED"
                        - option "DIMENSIONS · LINE · CF · BLOCKED"
                        - option "DIMENSIONS · LINE · D0 · BLOCKED"
                        - option "DIMENSIONS · TEXT · D1 · BLOCKED"
                        - option "DIMENSIONS · LINE · D2 · BLOCKED"
                        - option "DIMENSIONS · LINE · D3 · BLOCKED"
                        - option "DIMENSIONS · LINE · D4 · BLOCKED"
                        - option "DIMENSIONS · LINE · D5 · BLOCKED"
                        - option "DIMENSIONS · LINE · D6 · BLOCKED"
                        - option "DIMENSIONS · TEXT · D7 · BLOCKED"
                        - option "NOTES · TEXT · D8 · BLOCKED"
                        - option "NOTES · TEXT · D9 · BLOCKED"
                        - option "NOTES · TEXT · DA · BLOCKED"
                        - option "NOTES · TEXT · DB · BLOCKED"
                        - option "WARNINGS · TEXT · DC · BLOCKED"
                        - option "WARNINGS · TEXT · DD · BLOCKED"
                        - option "REAL_PROJECT"
                        - option "SYNTHETIC_VERIFICATION"
                        - option "UNVERIFIED" [selected]
                        - option "SLAB · LWPOLYLINE · handle 95" [selected]
                        - option "BEAMS · LWPOLYLINE · handle 96"
                        - option "BEAMS · LWPOLYLINE · handle 97"
                        - option "BEAMS · LWPOLYLINE · handle 98"
                        - option "BEAMS · LWPOLYLINE · handle 99"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · handle 9A"
                        - option "BASE_PLATES · LWPOLYLINE · handle 9B"
                        - option "COLUMNS · LWPOLYLINE · handle 9C"
                        - option "ANCHORS_DECLARED · CIRCLE · handle 9D"
                        - option "ANCHORS_DECLARED · CIRCLE · handle 9E"
                        - option "ANCHORS_DECLARED · CIRCLE · handle 9F"
                        - option "ANCHORS_DECLARED · CIRCLE · handle A0"
                        - option "CENTRELINES · LINE · handle A1"
                        - option "CENTRELINES · LINE · handle A2"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · handle A3"
                        - option "BASE_PLATES · LWPOLYLINE · handle A4"
                        - option "COLUMNS · LWPOLYLINE · handle A5"
                        - option "ANCHORS_DECLARED · CIRCLE · handle A6"
                        - option "ANCHORS_DECLARED · CIRCLE · handle A7"
                        - option "ANCHORS_DECLARED · CIRCLE · handle A8"
                        - option "ANCHORS_DECLARED · CIRCLE · handle A9"
                        - option "CENTRELINES · LINE · handle AA"
                        - option "CENTRELINES · LINE · handle AB"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · handle AC"
                        - option "BASE_PLATES · LWPOLYLINE · handle AD"
                        - option "COLUMNS · LWPOLYLINE · handle AE"
                        - option "ANCHORS_DECLARED · CIRCLE · handle AF"
                        - option "ANCHORS_DECLARED · CIRCLE · handle B0"
                        - option "ANCHORS_DECLARED · CIRCLE · handle B1"
                        - option "ANCHORS_DECLARED · CIRCLE · handle B2"
                        - option "CENTRELINES · LINE · handle B3"
                        - option "CENTRELINES · LINE · handle B4"
                        - option "FOOTINGS_CONCEPT · LWPOLYLINE · handle B5"
                        - option "BASE_PLATES · LWPOLYLINE · handle B6"
                        - option "COLUMNS · LWPOLYLINE · handle B7"
                        - option "ANCHORS_DECLARED · CIRCLE · handle B8"
                        - option "ANCHORS_DECLARED · CIRCLE · handle B9"
                        - option "ANCHORS_DECLARED · CIRCLE · handle BA"
                        - option "ANCHORS_DECLARED · CIRCLE · handle BB"
                        - option "CENTRELINES · LINE · handle BC"
                        - option "CENTRELINES · LINE · handle BD"
                        - option "STAIR_CONCEPT · LWPOLYLINE · handle BE"
                        - option "STAIR_CONCEPT · LINE · handle BF"
                        - option "STAIR_CONCEPT · LINE · handle C0"
                        - option "STAIR_CONCEPT · LINE · handle C1"
                        - option "STAIR_CONCEPT · LINE · handle C2"
                        - option "STAIR_CONCEPT · LINE · handle C3"
                        - option "STAIR_CONCEPT · LINE · handle C4"
                        - option "STAIR_CONCEPT · LINE · handle C5"
                        - option "STAIR_CONCEPT · LINE · handle C6"
                        - option "STAIR_CONCEPT · LINE · handle C7"
                        - option "STAIR_CONCEPT · LINE · handle C8"
                        - option "STAIR_CONCEPT · LINE · handle C9"
                        - option "STAIR_CONCEPT · LINE · handle CA"
                        - option "WARNINGS · TEXT · handle CB"
                        - option "DIMENSIONS · LINE · handle CC"
                        - option "DIMENSIONS · LINE · handle CD"
                        - option "DIMENSIONS · LINE · handle CE"
                        - option "DIMENSIONS · LINE · handle CF"
                        - option "DIMENSIONS · LINE · handle D0"
                        - option "DIMENSIONS · TEXT · handle D1"
                        - option "DIMENSIONS · LINE · handle D2"
                        - option "DIMENSIONS · LINE · handle D3"
                        - option "DIMENSIONS · LINE · handle D4"
                        - option "DIMENSIONS · LINE · handle D5"
                        - option "DIMENSIONS · LINE · handle D6"
                        - option "DIMENSIONS · TEXT · handle D7"
                        - option "NOTES · TEXT · handle D8"
                        - option "NOTES · TEXT · handle D9"
                        - option "NOTES · TEXT · handle DA"
                        - option "NOTES · TEXT · handle DB"
                        - option "WARNINGS · TEXT · handle DC"
                        - option "WARNINGS · TEXT · handle DD"
                        - option "UNVERIFIED"
                        - option "COLUMN"
                        - option "BEAM"
                        - option "SLAB" [selected]
                        - option "BASE_PLATE"
                        - option "FOUNDATION"
                        - option "ANCHOR_REFERENCE"
                        - option "UNVERIFIED"
                        - option "SYNTHETIC_VERIFICATION" [selected]
                        - option "REAL_PROJECT"
                        - option "No mapping declared"
                        - option "beam-east · industrial-platform-5x3:beam-east"
                        - option "beam-north · industrial-platform-5x3:beam-north"
                        - option "beam-south · industrial-platform-5x3:beam-south"
                        - option "beam-west · industrial-platform-5x3:beam-west"
                        - option "column-ne · industrial-platform-5x3:column-ne"
                        - option "column-nw · industrial-platform-5x3:column-nw"
                        - option "column-se · industrial-platform-5x3:column-se"
                        - option "column-sw · industrial-platform-5x3:column-sw"
                        - option "platform-deck · industrial-platform-5x3:platform-deck" [selected]
                        - option "foundation c9e0e256-1608-4be2-b1ab-adafa10424c0 · body · platform-addon:c9e0e256-1608-4be2-b1ab-adafa10424c0:body"
                        - option "base plate 44d566cb-7ca0-4c95-bf4d-1d574f788df0 · body · platform-addon:44d566cb-7ca0-4c95-bf4d-1d574f788df0:body"
                        - option "connection 149f0f5d-b98f-4260-a428-b2fc50959cf2 · joint · platform-addon:149f0f5d-b98f-4260-a428-b2fc50959cf2:joint"
                        - option "foundation b1ad97d4-faca-46e7-87c9-f5eebb37575f · body · platform-addon:b1ad97d4-faca-46e7-87c9-f5eebb37575f:body"
                        - option "base plate d9a7247f-b6fa-4e50-a3de-7a8c243f3dc3 · body · platform-addon:d9a7247f-b6fa-4e50-a3de-7a8c243f3dc3:body"
                        - option "connection 13ff4b82-88f8-4c41-9613-ad85bf72054b · joint · platform-addon:13ff4b82-88f8-4c41-9613-ad85bf72054b:joint"
                        - option "foundation 9c6c5059-9557-4c35-887a-a66e95606df4 · body · platform-addon:9c6c5059-9557-4c35-887a-a66e95606df4:body"
                        - option "base plate 2054528e-2362-4a24-843c-01988b6c8fea · body · platform-addon:2054528e-2362-4a24-843c-01988b6c8fea:body"
                        - option "connection a1f8b089-a278-4474-8596-ff0dade18975 · joint · platform-addon:a1f8b089-a278-4474-8596-ff0dade18975:joint"
                        - option "foundation 850c983b-9d8c-416d-8785-eb7106e068bb · body · platform-addon:850c983b-9d8c-416d-8785-eb7106e068bb:body"
                        - option "base plate b5d32b14-a981-4478-888f-42d19034592d · body · platform-addon:b5d32b14-a981-4478-888f-42d19034592d:body"
                        - option "connection ed0730b0-c13b-47ba-9753-b63f1e86d4ac · joint · platform-addon:ed0730b0-c13b-47ba-9753-b63f1e86d4ac:joint"
                        - option "brace b95d6eda-29f0-4b03-90ec-2c5b59199b8d · diagonal · platform-addon:b95d6eda-29f0-4b03-90ec-2c5b59199b8d:diagonal"
                        - option "brace 63a1eab7-ac09-4ceb-aaea-75c0427821e7 · diagonal · platform-addon:63a1eab7-ac09-4ceb-aaea-75c0427821e7:diagonal"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-1 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-1"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-2 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-2"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-3 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-3"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-4 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-4"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-5 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-5"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-6 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-6"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-7 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-7"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-8 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-8"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-9 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-9"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-10 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-10"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-11 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-11"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-12 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-12"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-13 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-13"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-14 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-14"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-15 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-15"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-16 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-16"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-17 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-17"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-18 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-18"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-19 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-19"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · tread-20 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:tread-20"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · stringer--1 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:stringer--1"
                        - option "stairs 664f80f7-3591-4b78-aecf-33ba6bc2fe5e · stringer-1 · platform-addon:664f80f7-3591-4b78-aecf-33ba6bc2fe5e:stringer-1"
                        - option "CAD column SW · drawing-cad:614f117ae2a74794:9C"
                        - option "CAD column SE · drawing-cad:614f117ae2a74794:AE"
                        - option "CAD beam South · drawing-cad:614f117ae2a74794:96"
                        - option "CAD slab · drawing-cad:614f117ae2a74794:95"
                        - option "CAD footing SW · drawing-cad:614f117ae2a74794:9A"
                        - option "CAD footing SE · drawing-cad:614f117ae2a74794:AC"
                        - option "CAD beam North · drawing-cad:614f117ae2a74794:97"
                        - option "CAD column NW · drawing-cad:614f117ae2a74794:A5"
                        - option "CAD column NE · drawing-cad:614f117ae2a74794:B7"
                        - option "CAD footing NW · drawing-cad:614f117ae2a74794:A3"
                        - option "CAD footing NE · drawing-cad:614f117ae2a74794:B5"
                        - option "symmetric"
                        - option "uniaxial"
                        - option "asymmetric"
                        - option "biaxial" [selected]
                        - option "2d_reduction"
                        - option "Declare / select explicitly" [selected]
                        - option "column-ne · industrial-platform-5x3:column-ne"
                        - option "column-nw · industrial-platform-5x3:column-nw"
                        - option "column-se · industrial-platform-5x3:column-se"
                        - option "column-sw · industrial-platform-5x3:column-sw"
                        - option "CAD column SW · drawing-cad:614f117ae2a74794:9C"
                        - option "CAD column SE · drawing-cad:614f117ae2a74794:AE"
                        - option "CAD column NW · drawing-cad:614f117ae2a74794:A5"
                        - option "CAD column NE · drawing-cad:614f117ae2a74794:B7"
                        - option "Declare / select explicitly" [selected]
                        - option "base plate 44d566cb-7ca0-4c95-bf4d-1d574f788df0 · body · platform-addon:44d566cb-7ca0-4c95-bf4d-1d574f788df0:body"
                        - option "base plate d9a7247f-b6fa-4e50-a3de-7a8c243f3dc3 · body · platform-addon:d9a7247f-b6fa-4e50-a3de-7a8c243f3dc3:body"
                        - option "base plate 2054528e-2362-4a24-843c-01988b6c8fea · body · platform-addon:2054528e-2362-4a24-843c-01988b6c8fea:body"
                        - option "base plate b5d32b14-a981-4478-888f-42d19034592d · body · platform-addon:b5d32b14-a981-4478-888f-42d19034592d:body"
                        - option "Declare / select explicitly" [selected]
                        - option "foundation c9e0e256-1608-4be2-b1ab-adafa10424c0 · body · platform-addon:c9e0e256-1608-4be2-b1ab-adafa10424c0:body"
                        - option "foundation b1ad97d4-faca-46e7-87c9-f5eebb37575f · body · platform-addon:b1ad97d4-faca-46e7-87c9-f5eebb37575f:body"
                        - option "foundation 9c6c5059-9557-4c35-887a-a66e95606df4 · body · platform-addon:9c6c5059-9557-4c35-887a-a66e95606df4:body"
                        - option "foundation 850c983b-9d8c-416d-8785-eb7106e068bb · body · platform-addon:850c983b-9d8c-416d-8785-eb7106e068bb:body"
                        - option "CAD footing SW · drawing-cad:614f117ae2a74794:9A"
                        - option "CAD footing SE · drawing-cad:614f117ae2a74794:AC"
                        - option "CAD footing NW · drawing-cad:614f117ae2a74794:A3"
                        - option "CAD footing NE · drawing-cad:614f117ae2a74794:B5"
                        - option "Declare / select explicitly" [selected]
                        - option "Declare / select explicitly" [selected]
                        - option "cube"
                        - option "cylinder"
                        - option "Declare / select explicitly" [selected]
                        - option "Not defined; reinforcement capacity excluded"
                        - option "Declared information; unverified"
                        - option "Declare / select explicitly" [selected]
                        - option "No geotechnical data; soil analysis excluded"
                        - option "Declared assumptions; unverified"
                        - option "Declare / select explicitly" [selected]
                        - option "No anchor definition; capacity excluded"
                        - option "New synthetic declared positions; unverified"
                        - option "Declare / select explicitly" [selected]
                        - option "Concentric full nominal contact, massless rigid plate"
                        - 'option "Rigid plate: assess actual N/M, no assumed full contact"'
                        - option "Declare / select explicitly" [selected]
                        - option "Isolate axial component; exclude actual V and M explicitly"
                        - option "Full reaction only if V=M=0 (otherwise rejected)"
                        - option "Actual N/M contact feasibility; shear transfer excluded"
                - tablist "Inspector views" [ref=e273]:
                  - tab "Layers" [ref=e274]
                  - tab "Inspect" [ref=e280]
                  - tab "History" [ref=e284]
                  - tab "Analysis" [selected] [ref=e290]
                  - tab "Review" [ref=e295]
        - region "Engineering dock" [ref=e300]:
          - generic [ref=e302]:
            - button "Engineering dock" [ref=e303]
            - button "Cost —" [ref=e308]:
              - 'generic "Cost: —" [ref=e309]':
                - generic [ref=e312]: Cost
                - generic [ref=e313]: —
            - button "Cement —" [ref=e315]:
              - 'generic "Cement: —" [ref=e316]':
                - generic [ref=e320]: Cement
                - generic [ref=e321]: —
            - button "Steel —" [ref=e323]:
              - 'generic "Steel: —" [ref=e324]':
                - generic [ref=e329]: Steel
                - generic [ref=e330]: —
            - button "Excavation —" [ref=e332]:
              - 'generic "Excavation: —" [ref=e333]':
                - generic [ref=e338]: Excavation
                - generic [ref=e339]: —
            - button "Duration —" [ref=e341]:
              - 'generic "Duration: —" [ref=e342]':
                - generic [ref=e346]: Duration
                - generic [ref=e347]: —
            - button "Area —" [ref=e349]:
              - 'generic "Area: —" [ref=e350]':
                - generic [ref=e354]: Area
                - generic [ref=e355]: —
            - button "Risk —" [ref=e357]:
              - 'generic "Risk: —" [ref=e358]':
                - generic [ref=e362]: Risk
                - generic [ref=e363]: —
  - button "Open Next.js Dev Tools" [ref=e369] [cursor=pointer]
  - alert [ref=e373]
```

# Test source

```ts
  1  | import {test,expect as pwExpect} from '@playwright/test';
  2  | import {writeFileSync} from 'node:fs';
  3  | const expect=pwExpect.configure({timeout:30000}),API='http://127.0.0.1:18001';
  4  | test.use({trace:'off'});
  5  | test('isolated foundation: separate study, exact review, two mats, report, alternatives, offline explanation and stale edits',async({page,request})=>{
  6  |  test.setTimeout(300000);page.setDefaultTimeout(30000);
  7  |  const attestation=await (await request.get(API+'/__foundation_validation')).json();expect(attestation.mode).toBe('foundation-isolated-20261015');expect(attestation.database.replaceAll('\\','/').endsWith('/docs/foundation-system/isolated/foundation.db')).toBe(true);
  8  |  expect(process.env.PLAYWRIGHT_BASE_URL).toContain(':13001');
  9  |  await page.route('**/api/geocode/map-runtime-config',r=>r.fulfill({json:{cesium_ion_token:null,google_maps_api_key:null}}));
  10 |  await page.route('**/*',async r=>{const u=r.request().url();if(/localhost:8001|127\.0\.0\.1:8001|\/local-api\//.test(u))throw new Error('Original backend forbidden in isolated browser');await r.fallback();});
  11 |  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  12 |  await page.setViewportSize({width:1600,height:1000});
  13 |  await page.goto('/projects/804/workspace');
  14 |  const canvas=page.locator('.cesium-widget canvas');await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  15 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();
  16 |  let panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  17 |  await expect(panel).toBeVisible();
> 18 |  const copyResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/copy')&&r.request().method()==='POST');
     |                          ^ TimeoutError: page.waitForResponse: Timeout 30000ms exceeded while waiting for event "response"
  19 |  await panel.getByRole('button',{name:'Create separate foundation study from 804'}).click();
  20 |  const response=await copyResponse;expect(response.ok(),await response.text()).toBeTruthy();const copy=await response.json();
  21 |  await page.waitForURL(`**/projects/${copy.project_id}/workspace`);
  22 |  await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});
  23 |  await page.getByRole('tab',{name:'Analysis',exact:true}).click();panel=page.getByRole('region',{name:'Integrated foundation workflow'});
  24 |  await expect(panel.getByLabel('Foundation code and edition')).toHaveValue('IS456-2000-A1A2');
  25 |  await expect(panel.getByRole('button',{name:'Preview integrated foundation calculation'})).toBeDisabled();
  26 |  await panel.getByLabel('Review foundation assumptions',{exact:true}).check();
  27 |  const previewResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/preview')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Preview integrated foundation calculation'}).click();
  28 |  const preview=await previewResponse;expect(preview.ok(),await preview.text()).toBeTruthy();const proposal=await preview.json();
  29 |  await expect(panel).toHaveAttribute('data-busy','false');
  30 |  await expect(panel.getByRole('button',{name:'Save reviewed foundation result'})).toBeDisabled();
  31 |  await panel.getByLabel('Authorize exact foundation calculation',{exact:true}).check();
  32 |  const authResponse=page.waitForResponse(r=>r.url().endsWith('/foundation-system/authorize')&&r.request().method()==='POST');await panel.getByRole('button',{name:'Save reviewed foundation result'}).click();const auth=await authResponse;expect(auth.ok(),await auth.text()).toBeTruthy();const result=await auth.json();
  33 |  const output=panel.getByRole('article',{name:'Foundation visual analysis'});await expect(output).toContainText('Exceeds implemented check');expect(result.result.computed.rc.layers.map((l:{effective_depth_mm:number})=>l.effective_depth_mm)).toEqual([365,345]);
  34 |  await output.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(1000);
  35 |  await page.screenshot({path:'../docs/foundation-visual/system-regression-3d-foundation-1600.png'});
  36 |  await panel.getByText('Reports, methods and immutable evidence',{exact:true}).click();const download=page.waitForEvent('download');await panel.getByRole('button',{name:'Download calculation report'}).click();const file=await download;await file.saveAs('../docs/foundation-visual/system-regression-browser-calculation-report.html');
  37 |  await output.getByRole('button',{name:'Foundation alternatives',exact:true}).click();await output.getByRole('button',{name:'Calculate validated comparisons'}).click();await expect(output.getByRole('button',{name:'Review selected alternative'})).toBeVisible();
  38 |  const assistant=page.getByRole('region',{name:'Project assistant',exact:true});if(!await assistant.isVisible())await page.getByRole('button',{name:'Show AI Copilot panel',exact:true}).click();const input=assistant.getByRole('textbox',{name:'Project message'});await expect(input).toBeEnabled({timeout:30000});await input.fill('Explain saved foundation reinforcement, punching and supported alternatives');await page.getByRole('button',{name:'Send message',exact:true}).click();await expect(assistant.getByRole('article',{name:'Assistant message'}).last()).toContainText('Saved foundation evidence #',{timeout:60000});await expect(assistant.getByText(/chat cannot apply or authorize/).first()).toBeVisible();
  39 |  await page.screenshot({path:'../docs/foundation-visual/system-regression-offline-copilot-1600.png'});
  40 |  if(await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).isVisible())await page.getByRole('button',{name:'Hide AI Copilot panel',exact:true}).click();await page.getByRole('tab',{name:'Analysis',exact:true}).click();await panel.getByText('Inputs, proposals and authorization',{exact:true}).click();await panel.getByText('Actions, materials, soil and detailing inputs',{exact:true}).click();await panel.getByLabel('Independent factored column action kN',{exact:true}).fill('432');await expect(output).toHaveAttribute('data-stale','true');await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');await expect(panel.locator('button').filter({hasText:'Download calculation report'})).toBeDisabled();
  41 |  await page.reload();await expect(canvas).toHaveAttribute('data-sandbox-ready','true',{timeout:90000});await page.getByRole('tab',{name:'Analysis',exact:true}).click();await expect(output).toHaveAttribute('data-stale','false');
  42 |  await page.setViewportSize({width:1280,height:900});await output.getByRole('button',{name:'Reinforcement and anchorage',exact:true}).click();await expect(canvas).toHaveAttribute('data-elastic-diagram','foundation-integrated');await page.waitForTimeout(800);await page.screenshot({path:'../docs/foundation-visual/system-regression-3d-foundation-1280.png'});
  43 |  await panel.getByRole('button',{name:'Restore full model from foundation view'}).click();await expect(canvas).not.toHaveAttribute('data-elastic-diagram','foundation-integrated');
  44 |  expect(errors).toEqual([]);
  45 |  writeFileSync('../docs/foundation-visual/system-regression-browser-results.json',JSON.stringify({attestation,copy,proposal_id:proposal.id,result_id:result.id,two_mats:true,download:true,alternatives:true,offline_copilot:true,stale_edit_clears_overlay:true,reload:true,page_errors:errors},null,2));
  46 | });
  47 | 
```