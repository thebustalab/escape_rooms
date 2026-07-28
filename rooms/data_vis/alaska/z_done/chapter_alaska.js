/*
 * chapter_alaska.js — content for the Alaska chapter ("Signal in the Cold").
 *
 * Data only; the flow lives in play.html. A chapter is a chain of pseudo-360 pano
 * rooms: each has one practice puzzle (a WebR editor task gated by a multiple-choice
 * answer that is the *product* of running the analysis) and a door that opens on
 * solve and leads to the next room. This chapter drills dplyr::filter(); the boss
 * (room 4, the helipad) is a figure deliverable — not built in this slice.
 *
 * Hotspot positions are boxes [x0,y0,x1,y1] as fractions of the flat scene image
 * (same convention as the harness); the viewer maps box-centre -> yaw/pitch across
 * the room's wrap coverage. Nudge them in the harness later if needed.
 */
window.CHAPTER = {
  id: 6,
  title: "Signal in the Cold",
  subtitle: "Chapter 1 · practising filter()",
  story:
    "A faint distress ping is bouncing around the Noatak backcountry. You're the analyst " +
    "on shift at the dispatch cabin: work the field data room by room, and each door only " +
    "opens once you've pulled the right numbers out of R.",
  enterLabel: "Enter the cabin →",
  done: {
    title: "Room 1 cleared",
    body: "You pulled the Noatak rows and the door gave way. Rooms 2 and 3 (tougher filter() " +
      "work, then a plot) and the boss — the helicopter pad — come next.",
  },

  // one WebR session, booted once on entry and shared by every room
  packages: ["dplyr", "readr"],
  datasets: [
    { name: "alaska_lake_data",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/alaska_lake_data.csv" },
  ],
  setup: "suppressMessages(library(dplyr))",

  rooms: [
    {
      key: "room1",
      title: "The dispatch cabin",
      panorama: "_scratch/gpt_gen_5.png",
      panoramaOpen: "_scratch/gpt_gen_5_open.png",
      wrap: { haov: 360, vaov: 90, hfov: 120, vOffset: -5, pitch: -6.1 },
      // boxes authored in the harness for gpt_gen_5 (harness coverage haov 360 / vaov 90 / vOffset -5)
      hotspots: [
        {
          id: "note", type: "clue", label: "A pinned note",
          box: [0.2621, 0.4507, 0.2824, 0.5332],
          body:
            "A scrap pinned to the corkboard, hand-scrawled: <em>“Ping origin = NOAT sector. " +
            "Ignore GAAR / BELA traffic.”</em> Three preserves feed the board — Gates of the " +
            "Arctic (GAAR), Bering Land Bridge (BELA) and Noatak (<b>NOAT</b>) — but you only " +
            "want the Noatak rows.",
        },
        {
          id: "laptop", type: "puzzle", label: "The dispatch laptop",
          box: [0.424, 0.5691, 0.4586, 0.6546],
          starterCode:
            'library(dplyr)\n\n' +
            '# The ping is in the Noatak preserve (park == "NOAT").\n' +
            '# Filter the lake data to just those rows, then read the\n' +
            '# tibble header — it prints "A tibble: N x 7".\n\n' +
            'alaska_lake_data %>%\n' +
            '  filter(park == "____")\n',
          question: {
            prompt:
              'Keep only the Noatak-preserve rows: <code>filter(park == "NOAT")</code>, and run it. ' +
              'The tibble header reads “A&nbsp;tibble: N&nbsp;×&nbsp;7”. What is N — how many rows remain?',
            options: ["44", "55", "66", "99"],
            correct: 1,
            maxAttempts: 4,
            feedback: {
              correct:
                "55 rows — the Noatak measurements. Something clunks in the door frame behind you.",
              wrong: [
                'Read the “N × 7” at the very top of the tibble after filtering. Is the condition exactly <code>park == "NOAT"</code>? (It’s case-sensitive.)',
                "66 is BELA and 99 is GAAR — you may have filtered the wrong preserve. Re-check the park code.",
                'Run <code>alaska_lake_data %>% filter(park == "NOAT")</code> and read the row count in the header line.',
              ],
              reveal: 'It’s <b>55</b> — <code>filter(park == "NOAT")</code> keeps 55 rows.',
            },
          },
        },
        {
          id: "door", type: "door", label: "The cabin door",
          box: [0.6012, 0.3466, 0.6542, 0.7194],
        },
      ],
    },

    // rooms 2 and 3 (multi-condition filter, then filter + a basic plot) and the
    // boss helipad (figure + buildCaption() deliverable) are authored next.
  ],
};
