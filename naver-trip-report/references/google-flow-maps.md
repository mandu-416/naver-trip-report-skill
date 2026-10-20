# Drawing day maps in Google Flow

Google Flow (flow.google.com) is driven through the user's own logged-in Chrome (Claude in Chrome tools). The image model used was Nano Banana; each prompt returns two images.

## Procedure

1. Open a new tab, go to `https://flow.google.com`, open or create a project. The prompt box is labelled "무엇을 만들고 싶으신가요?" and the submit button "생성 시작".
2. Submit one prompt per day. Several prompts can be queued back to back; each takes roughly 40–60 s.
3. Open each result (click the tile). The edit box is labelled "어떤 내용을 변경하려 하시나요?". Send the Korean relabel edit (template below). Edits replace the image in place, keeping its id.
4. Long `type` actions sometimes time out ("Input.dispatchKeyEvent timed out") even though the text was entered, and the page can freeze for 10–30 s while rendering. Take a screenshot to confirm the full prompt is in the box, then click the submit button found with `find` instead of pressing Enter.
5. Navigating straight to an `/edit/<id>` URL may bounce back to the last image. Use the thumbnail strip at the top of the edit view (`find` → "image thumbnails in the top strip") to switch images.
6. Download (only after the user agrees): the download icon in the edit view's top bar → "1K 원본 크기". Files land in the user's Downloads folder with English auto-titles plus a timestamp; map them to days by download order or by viewing them.

## Prompt template (first generation)

```
Clean flat illustrated travel map, landscape 16:9, of <area list>, north at top,
soft pastel colors, legible text. Title at top: "<N일차 MM/DD(요일) 테마>".
Draw a bold red numbered walking route with circular pins in this order:
1 "<시간> <장소> – <한 줄 설명>"; 2 "..."; ...
Hotel icon "숙소 <hotel>" at <relative position>.
Add small orange fork-and-knife restaurant markers labeled "<식당 – 메뉴 가격>", ... near <area>.
Small legend: red pin = 일정, orange fork = 식당. White label cards next to each pin, minimal clutter.
```

Variations that worked:

- Out-of-town or tour days: a split layout (left: regional map with a purple tour line; right: small inset of the city evening route).
- A venue far from the core area (e.g. an Olympic pool): a small inset box in a corner with a dotted arrow to the first city stop.
- Running routes: a green dashed line with its own legend entry; spell out the exact path ("from Circular Quay through The Rocks onto the Harbour Bridge to Kirribilli and back") or the model invents a loop.
- Ferry legs: a blue dashed line.

Give relative positions for every pin (north/south/east/west of a landmark). The model places things by these hints; without them pins drift.

## Korean relabel edit (second pass)

```
Keep the map, routes, pins, icons and layout exactly the same. Only rewrite all label text
in Korean, crisp and correctly spelled Hangul: title "<...>"; 1 "<...>"; 2 "<...>"; ...;
restaurants "<...>", "<...>"; legend "<...>". Keep English place names on the base map.
```

Add any geometric fix to the same edit ("change the dotted arrow so it points to pin 2", "remove the duplicate label"). Expect small transliteration oddities ("피트니스", "숙 샌드위치") and occasional pin drift; list what's still wrong in the reply.
