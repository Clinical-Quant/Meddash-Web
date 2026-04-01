# Plan: Verify Mermaid Viewer Zoom/Pan Controls

1. [x] Navigate to http://localhost:8000
    - Findings: http://localhost:8000 returns Meddash API JSON, not the frontend.
    - Path `file:///c:/Users/email/.../index.html` is blocked.
2. [ ] Find the correct URL for the Mermaid Viewer.
3. [ ] Wait 3 seconds for rendering
4. [ ] Verify editor on left, diagram on right
5. [ ] Verify zoom buttons (+, %, -, Reset, Fit)
6. [ ] Click "+" 3 times, check zoom %
7. [ ] Click "-" 2 times
8. [ ] Click "Fit"
9. [ ] Click "Reset"
10. [ ] Test mousewheel scroll zoom
11. [ ] Test drag-to-pan
12. [ ] Report findings with screenshots

## Attempted URLs:
- http://localhost:8000 (API)
- http://localhost:8000/index.html (likely API)
- http://localhost:3000 (Meddash Phase 2 UI)
- http://localhost:8080 (Refused)
- http://localhost:8001 (Refused)
- file:/// (Blocked)
