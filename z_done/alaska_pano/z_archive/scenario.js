/*
 * scenario.js — "Signal in the Cold: The Cabin" (PANORAMA explore prototype).
 *
 * flow: "explore" with a single cohesive room panorama sliced into 4 facings you
 * pan across (‹ ›). Each facing has an optional `action` (a labelled button that
 * opens a clue or the room's multiple-choice question). One facing is the DOOR:
 * `door:true` with an `openImage`. Solving the room's question swaps the door
 * facing to its open image and shows a "^ Go through" button to the next room.
 *
 * Art: authoring/prompts/alaska_pano_room1.txt -> generate_scene.py gen, then
 * `slice` into desk/bulletin/kitchen/door_closed; door_open via `edit` on the
 * whole panorama, sliced to the door quarter.
 */
window.SCENARIO = {
  id: 5,
  slug: "alaska_pano",
  title: "Signal in the Cold — The Cabin",
  flow: "explore",

  packages: ["readr", "dplyr", "ggplot2"],
  datasets: [
    { name: "alaska_lake_data",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/alaska_lake_data.csv" },
  ],
  setup: "suppressMessages({library(readr); library(dplyr); library(ggplot2)})",

  screen1: {
    image: "scene/desk.png",
    title: "Noatak Search & Rescue — 02:14",
    story: `
      <p>A bush plane is down in the Noatak Preserve, and the beacon is still
      transmitting hours past the point anyone should survive the cold. The cabin
      holds what you need — look around it, find the analysis, and follow the
      trail through.</p>
      <p>Use the ‹ › arrows to turn around the room. Examine what you find; answer
      the one real question to open the door onward.</p>
      <p class="byline">Enter your x500 to sign the case log, then step inside.</p>
    `,
    enterLabel: "Enter the cabin →",
  },

  briefing: `
    <p><code>alaska_lake_data</code> is loaded (columns include <code>lake</code>,
    <code>park</code>, <code>water_temp</code>). Do your analysis in the pop-up
    console when you examine the desk.</p>
  `,

  rooms: [
    {
      key: "cabin",
      title: "The Cabin",
      // One panorama, sliced + drawn live on a canvas (facing 3 is the door).
      // Tuned in tune.html: overlap 150, crop-height 920, blur 30, contain.
      panorama: "scene/_pano.png",
      panoramaOpen: "scene/_pano_open.png",
      facings: 4,
      doorFacing: 3,
      slice: { overlap: 150, cropHeight: 920 },
      blur: 30,
      starterCode:
        'library(dplyr)\nlibrary(ggplot2)\n\nalaska_lake_data %>%\n  filter(park == "NOAT") %>%\n  ggplot() +\n  geom_point(aes(x = water_temp, y = lake))',
      actions: {
        "0": {
          type: "question",
          label: "Examine the desk",
          starterCode:
            'library(dplyr)\nlibrary(ggplot2)\n\nalaska_lake_data %>%\n  filter(park == "NOAT") %>%\n  ggplot() +\n  geom_point(aes(x = water_temp, y = lake))',
          prompt:
            "The laptop is open to the lake survey. Filter to Noatak (<code>park == \"NOAT\"</code>) and compare water temperature across lakes. Which lake should the team search first?",
          options: [
            "Devil_Mountain_Lake", "Imuruk_Lake", "Kuzitrin_Lake", "Lava_Lake",
            "North_Killeak_Lake", "White_Fish_Lake", "Iniakuk_Lake", "Kurupa_Lake",
            "Lake_Matcharak", "Lake_Selby", "Nutavukti_Lake", "Summit_Lake",
            "Takahula_Lake", "Walker_Lake", "Wild_Lake", "Desperation_Lake",
            "Feniak_Lake", "Lake_Kangilipak", "Lake_Narvakrak", "Okoklik_Lake",
          ],
          correct: 18, maxAttempts: 4,
          feedback: {
            correct: "That's it — <strong>Lake Narvakrak</strong> sits far above the rest. Somewhere a latch clicks — the door has opened.",
            wrong: [
              "Filter to <code>park == \"NOAT\"</code> first, then look for the point far to the right.",
              "Map temperature to x and lake to y so the outlier stands out.",
              "One Noatak lake is near 18&nbsp;°C while the others sit below 7&nbsp;°C.",
            ],
            reveal: "The warm outlier was <strong>Lake Narvakrak</strong>. Recording your answer.",
          },
        },
        "1": {
          type: "clue", label: "Read the bulletin board",
          body: "Among the pinned notes, one is circled twice: <em>“Beacon still live at 04:00 — impossible in this cold unless the water near him runs warm.”</em>",
        },
        "2": {
          type: "clue", label: "Search the kitchen",
          body: "A field logbook lies open by the kettle: <em>“Most Noatak lakes read 3–6 °C tonight. One reads nothing like the others.”</em>",
        },
      },
    },
    {
      key: "back_room",
      title: "The Back Room",
      views: [
        {
          image: "scene/backroom.png",
          action: {
            type: "question",
            label: "Examine the radio",
            prompt:
              "Through the door, the radio set is still receiving. The beacon kept transmitting for hours, long past the 25-minute cold-water window. Given what you found next door, what is the most likely explanation?",
            options: [
              "The beacon simply malfunctioned and the reading means nothing.",
              "Ethan reached the one unusually warm lake, which kept him alive.",
              "The cold slowed the beacon's battery, faking a long signal.",
              "Another aircraft's beacon was overlapping the frequency.",
            ],
            correct: 1, maxAttempts: 2,
            feedback: {
              correct: "Exactly — a warm lake in a freezing preserve is the one place a survival timeline stretches to hours.",
              wrong: [
                "Tie it to your finding: one lake is far warmer than the rest. What would that mean for someone in the water?",
              ],
              reveal: "The intended reading: the warm lake explains the long signal.",
            },
          },
        },
      ],
    },
  ],

  finishMessage: `
    <p>The trail runs from the warm lake to the impossible signal — the search is
    narrowed to <strong>Lake Narvakrak</strong>. Copy your case code below and
    submit it to Canvas.</p>
  `,
};
