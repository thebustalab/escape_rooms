/*
 * scenario.js — "Signal in the Cold: The Station" (EXPLORE-mode prototype).
 *
 * flow: "explore" — a case is several ROOMS worked in order. Each room has a set
 * of `views` (images) the student pans between with ‹ › arrows, and `artifacts`
 * placed on those views: `type:"clue"` (flavour/hint text) or `type:"question"`
 * (the real multiple-choice — one per room). Solving a room's question opens the
 * door onward; the last room ends the case.
 *
 * This is a NAVIGATION prototype (per Lucas): the R-console problems come later.
 * Question content reuses the Alaska data-viz case (answers 18 / 3 / 1).
 * Artifact `pos` are {x,y} % on the current view — nudge to sit on the object.
 */
window.SCENARIO = {
  id: 4,
  slug: "alaska_station",
  title: "Signal in the Cold — The Station",
  flow: "explore",

  packages: ["readr", "dplyr", "ggplot2"],
  datasets: [
    { name: "alaska_lake_data",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/alaska_lake_data.csv" },
  ],
  setup: "suppressMessages({library(readr); library(dplyr); library(ggplot2)})",

  screen1: {
    image: "scene/map_v1.png",
    title: "Noatak Search & Rescue — 02:14",
    story: `
      <p>A bush plane is down in the Noatak Preserve, and the beacon is still
      transmitting hours past the point anyone should survive the cold. The answer
      is somewhere in this station — spread across three rooms.</p>
      <p>Look around each room with the ‹ › arrows, examine what you find, and
      answer the one real question in each to open the way to the next.</p>
      <p class="byline">Enter your x500 to sign the case log, then step inside.</p>
    `,
    enterLabel: "Enter the station →",
  },

  briefing: `
    <p>The dataset <code>alaska_lake_data</code> is loaded (columns include
    <code>lake</code>, <code>park</code>, <code>water_temp</code>). Explore the
    rooms on the right; each holds a clue and one question.</p>
  `,

  rooms: [
    {
      key: "map_room",
      title: "The Map Room",
      starterCode:
        'library(dplyr)\nlibrary(ggplot2)\n\nalaska_lake_data %>%\n  filter(park == "NOAT") %>%\n  ggplot() +\n  geom_point(aes(x = water_temp, y = lake))',
      views: [
        { image: "scene/map_v0.png" }, // clue: corkboard note
        { image: "scene/map_v1.png" }, // question: wall map + laptop
        { image: "scene/map_v2.png" }, // atmosphere: shelves + window
      ],
      artifacts: [
        { view: 0, pos: { x: 50, y: 55 }, type: "clue", label: "Pinned note",
          body: "A curling note reads: <em>“Beacon still live at 04:00. Impossible in this cold — unless the water near him runs warm.”</em>" },
        { view: 1, pos: { x: 47, y: 62 }, type: "question", label: "The lake map & laptop",
          prompt: "Filter to Noatak (<code>park == \"NOAT\"</code>) and compare water temperature across lakes. Which lake should the team search first?",
          options: [
            "Devil_Mountain_Lake", "Imuruk_Lake", "Kuzitrin_Lake", "Lava_Lake",
            "North_Killeak_Lake", "White_Fish_Lake", "Iniakuk_Lake", "Kurupa_Lake",
            "Lake_Matcharak", "Lake_Selby", "Nutavukti_Lake", "Summit_Lake",
            "Takahula_Lake", "Walker_Lake", "Wild_Lake", "Desperation_Lake",
            "Feniak_Lake", "Lake_Kangilipak", "Lake_Narvakrak", "Okoklik_Lake",
          ],
          correct: 18, maxAttempts: 4,
          feedback: {
            correct: "That's it — <strong>Lake Narvakrak</strong> sits far above the rest. A door clicks open.",
            wrong: [
              "Filter to <code>park == \"NOAT\"</code> first, then look for the point far to the right.",
              "Map temperature to x and lake to y so the outlier stands out.",
              "One Noatak lake is near 18&nbsp;°C while the others sit below 7&nbsp;°C.",
            ],
            reveal: "The warm outlier was <strong>Lake Narvakrak</strong>. Recording your answer.",
          } },
      ],
    },
    {
      key: "readout_room",
      title: "The Readout Room",
      views: [
        { image: "scene/read_v0.png" }, // clue: logbook
        { image: "scene/read_v1.png" }, // question: temperature readout
        { image: "scene/read_v2.png" }, // atmosphere: gear
      ],
      artifacts: [
        { view: 0, pos: { x: 50, y: 56 }, type: "clue", label: "Field logbook",
          body: "The last entry: <em>“Most Noatak lakes read 3–6 °C tonight. One reads nothing like the others.”</em>" },
        { view: 1, pos: { x: 38, y: 52 }, type: "question", label: "The temperature readout",
          prompt: "Roughly how warm is that outlier lake, compared with the others clustered together?",
          options: ["About 3 °C", "About 6 °C", "About 12 °C", "About 18 °C"],
          correct: 3, maxAttempts: 3,
          feedback: {
            correct: "Right — about <strong>18&nbsp;°C</strong>, while the rest sit near freezing.",
            wrong: [
              "Read the position of the outlier off the chart.",
              "The others cluster around 3–6&nbsp;°C; the outlier is far beyond them.",
            ],
            reveal: "It reads close to 18&nbsp;°C. Recording your answer.",
          } },
      ],
    },
    {
      key: "radio_room",
      title: "The Radio Room",
      views: [
        { image: "scene/radio_v0.png" }, // clue: radio log
        { image: "scene/radio_v1.png" }, // question: beacon receiver
        { image: "scene/radio_v2.png" }, // atmosphere: door to helipad
      ],
      artifacts: [
        { view: 0, pos: { x: 50, y: 55 }, type: "clue", label: "Radio log",
          body: "Timestamps march down the page — the beacon has pinged every ten minutes, steady, for hours." },
        { view: 1, pos: { x: 55, y: 60 }, type: "question", label: "The beacon receiver",
          prompt: "The beacon kept transmitting for hours, long past the 25-minute cold-water window. Given what you found, what is the most likely explanation?",
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
          } },
      ],
    },
  ],

  finishMessage: `
    <p>Three rooms, three findings — the search is narrowed to <strong>Lake
    Narvakrak</strong>. Copy your case code below and submit it to Canvas.</p>
  `,
};
