# naver-trip-report (Claude Code skill)

네이버 블로그와 구글 검색 결과를 Firecrawl로 크롤링해서, **시간 계산이 들어간 일자별 여행 동선 보고서**를 만들어 주는 Claude Code 스킬입니다.

- 확정된 투어, 숙소, 도착·출국 시간에 맞춰 관광지, 쇼핑, 운동(수영·헬스, 새벽 러닝)을 배치합니다.
- 끼니마다 동선 근처의 저렴한 현지인 식당 3곳을 출처 링크와 함께 추천합니다.
- 요일별 휴무와 영업시간을 확인하고, 숙소 기준 이동 시간 표를 만듭니다.
- Google Flow로 일자별 동선 지도(번호 핀, 장소 설명, 식당 표시)를 그려 보고서에 넣습니다.

## 설치

```bash
# 사용자 전체에 설치
cp -r naver-trip-report ~/.claude/skills/
# 또는 프로젝트에만 설치
cp -r naver-trip-report <프로젝트>/.claude/skills/
```

작업 폴더의 `.env`에 Firecrawl API 키를 넣으세요. `.env`는 커밋하지 마세요.

```
FIRECRAWL_API_KEY=fc-...
```

## 필요한 것

- [Firecrawl](https://firecrawl.dev) API 키
- Python 3 (표준 라이브러리만 사용)
- 지도를 그리려면 Claude in Chrome 확장과 Google Flow에 로그인된 Chrome
- 공유 가능한 문서로 만들려면 Claude Docs 커넥터 (없으면 Markdown/HTML로 작성)

## 사용 예

```
네이버에서 시드니 시내 쇼핑코스 크롤링해줘
11/5~11/10 일정이야. 금·월은 투어 예약돼 있고 숙소는 OO호텔이야. 수영·헬스랑 새벽 러닝 넣어서 일정 보고서 써줘
일정 사이에 저렴한 현지인 식당 3개씩 넣어줘
1~5일차 동선을 Google Flow로 지도 그려서 보고서에 넣어줘
```

## 요청 제한과 자동 재시도

Firecrawl은 짧은 시간에 요청이 몰리면 요청 제한(HTTP 429)을 겁니다. 크롤러는 이런 경우 자동으로 다시 시도합니다.

- **다시 시도하는 오류:** 요청 제한(429), 일시적인 서버 오류(500·502·503·504), 네트워크 타임아웃
- **횟수와 간격:** 최대 5번까지 다시 시도합니다. 서버가 기다릴 시간(`Retry-After`)을 알려주면 그만큼 기다리고, 아니면 5, 10, 20, 40, 60초로 간격을 늘립니다.
- **바로 실패하는 오류:** 404처럼 다시 해도 소용없는 오류는 재시도하지 않습니다.
- **동시 요청 수:** 블로그 본문은 기본 3개씩 동시에 받습니다. `--workers` 옵션으로 바꿀 수 있습니다.

```bash
python -I naver-trip-report/scripts/naver_crawl.py posts work/posts.txt --limit 6 --workers 2 --out work/posts
```

스크립트를 여러 개 동시에 실행하면 재시도가 있어도 제한에 계속 걸릴 수 있습니다. 검색은 몇 개씩 나눠 돌리고, 본문 수집은 `posts` 명령 하나로 맡기세요.

## 구성

```
naver-trip-report/
├── SKILL.md                         # 작업 순서와 판단 기준
├── scripts/naver_crawl.py           # 네이버 검색·블로그 본문·구글 검색 크롤러 (Firecrawl)
└── references/google-flow-maps.md   # Google Flow 지도 프롬프트 템플릿과 브라우저 조작 요령
```

## 주의

- AI가 그린 지도라 위치와 거리는 대략적입니다. 길을 찾을 때는 구글 지도를 함께 보세요.
- 블로그 글 중에는 제휴·광고 글이 섞여 있을 수 있습니다. 스킬이 보고서에 표시해 줍니다.
- 가격과 영업시간은 출처 글이 쓰인 시점 기준입니다. 방문 전에 다시 확인하세요.

## License

MIT
