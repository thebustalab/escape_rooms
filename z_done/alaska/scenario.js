/*
 * scenario.js — "Signal in the Cold" (Alaska lake mystery).
 *
 * A scenario is pure data. To add a new mystery, copy this file, change the
 * id (keep it unique, 1-15), the story, datasets, packages, and steps — the
 * engine and codec do the rest.
 *
 * Step encoding note: `correct` is a 0-based index into `options`, and must be
 * 0-31 (5 bits). Keep option lists to 32 or fewer.
 */
window.SCENARIO = {
  id: 1,
  slug: "alaska",
  title: "Signal in the Cold",

  // Optional ambience. `music` plays from the moment the student clicks Enter
  // (a user gesture, which satisfies browser autoplay rules) and loops quietly.
  // `keepBackground: true` carries screen 1's image into screen 2 as a dimmed
  // backdrop. Drop a track at alaska/audio/ and point `music` at it; leave
  // `music` null for silence.
  music: "audio/ambience.mp3",
  musicVolume: 0.35,
  keepBackground: true,

  packages: ["readr", "dplyr", "ggplot2"],
  datasets: [
    {
      name: "alaska_lake_data",
      url: "https://thebustalab.github.io/phylochemistry/sample_data/alaska_lake_data.csv",
    },
  ],
  setup: "suppressMessages({library(readr); library(dplyr); library(ggplot2)})",

  screen1: {
    image: "https://cdn.midjourney.com/6b9bdd4a-5852-41ba-83a7-41762e6c29d7/0_0.png",
    title: "Noatak National Preserve — 02:14",
    story: `
      <p>Ethan Sawyer's bush plane went down hours ago in the Noatak National
      Preserve. In water this cold, a person lasts about <strong>25 minutes</strong>.
      Yet his emergency beacon is <em>still transmitting</em>.</p>
      <p>"That doesn't make sense," says Sarah, the search coordinator. Across the
      table, Dr. Ryan Caldwell adjusts his glasses. "Unless," he says slowly,
      "he landed near something warm."</p>
      <p>Noatak's lakes are glacial — freezing, all of them. But if just one lake
      runs warmer than the rest, that is where the rescue team should look first.
      Ryan opens the water-chemistry survey on his laptop. There are a lot of
      lakes, and not much time.</p>
      <p class="byline">Enter your x500 to sign the case log, then step inside.</p>
    `,
    enterLabel: "Enter the Search & Rescue station →",
  },

  briefing: `
    <p>The dataset <code>alaska_lake_data</code> is already loaded. Each row is a
    measurement from a lake, with columns including <code>lake</code>,
    <code>park</code> (the preserve code), and <code>water_temp</code>.</p>
    <p>Noatak National Preserve has the park code <code>NOAT</code>. Use the console
    to explore, then answer the case questions on the right. There is no penalty
    for exploring — only for guessing.</p>
  `,

  starterCode:
    'library(dplyr)\nlibrary(ggplot2)\n\n# Focus on Noatak (park code "NOAT") and compare lake temperatures\nalaska_lake_data %>%\n  filter(park == "NOAT") %>%\n  ggplot() +\n  geom_point(aes(x = water_temp, y = lake))',

  steps: [
    {
      prompt:
        "Filter to Noatak (<code>park == \"NOAT\"</code>) and compare water temperature across lakes. One lake is dramatically warmer than the rest. Which lake should the team search first?",
      options: [
        "Devil_Mountain_Lake", "Imuruk_Lake", "Kuzitrin_Lake", "Lava_Lake",
        "North_Killeak_Lake", "White_Fish_Lake", "Iniakuk_Lake", "Kurupa_Lake",
        "Lake_Matcharak", "Lake_Selby", "Nutavukti_Lake", "Summit_Lake",
        "Takahula_Lake", "Walker_Lake", "Wild_Lake", "Desperation_Lake",
        "Feniak_Lake", "Lake_Kangilipak", "Lake_Narvakrak", "Okoklik_Lake",
      ],
      correct: 18, // Lake_Narvakrak
      maxAttempts: 4,
      feedback: {
        correct:
          "That's it — <strong>Lake Narvakrak</strong> sits far above every other Noatak lake. Send the team there.",
        wrong: [
          "Make sure you've filtered to <code>park == \"NOAT\"</code> first — other preserves have their own lakes. Then look for the single point far to the right.",
          "Try mapping temperature to the x-axis and lake to the y-axis so the outlier is easy to spot: <code>geom_point(aes(x = water_temp, y = lake))</code>.",
          "One Noatak lake is near 18&nbsp;°C while the others sit below 7&nbsp;°C. Which one?",
        ],
        reveal:
          "The warm outlier was <strong>Lake Narvakrak</strong> (~18&nbsp;°C). We'll record your last answer and move on.",
      },
    },
    {
      prompt:
        "Roughly how warm is that outlier lake, compared with the others clustered together?",
      options: [
        "About 3 °C", "About 6 °C", "About 12 °C", "About 18 °C",
      ],
      correct: 3,
      maxAttempts: 3,
      feedback: {
        correct:
          "Right — about <strong>18&nbsp;°C</strong>, while the rest of Noatak sits near freezing. A genuine thermal anomaly.",
        wrong: [
          "Read the x-position of the outlier point off your plot.",
          "The other lakes cluster around 3–6&nbsp;°C; the outlier is far to the right of them.",
        ],
        reveal: "It reads close to 18&nbsp;°C. Moving on.",
      },
    },
    {
      prompt:
        "The beacon kept transmitting for hours, long past the 25-minute cold-water survival window. Given what you found, what is the most likely explanation?",
      options: [
        "The beacon simply malfunctioned and the reading means nothing.",
        "Ethan reached the one unusually warm lake, which kept him alive.",
        "The cold slowed the beacon's battery, faking a long signal.",
        "Another aircraft's beacon was overlapping the frequency.",
      ],
      correct: 1,
      maxAttempts: 2,
      feedback: {
        correct:
          "Exactly the inference Ryan made — a warm lake in a freezing preserve is the one place a survival timeline stretches to hours. That's where they search.",
        wrong: [
          "Tie it back to your finding: you just showed one lake is far warmer than the rest. What would that mean for someone in the water?",
        ],
        reveal:
          "The intended reading: the warm lake explains the impossibly long signal. Moving on.",
      },
    },
  ],

  finishMessage: `
    <p>You narrowed the search to <strong>Lake Narvakrak</strong> and explained the
    impossible signal. Ryan is already radioing the coordinates.</p>
    <p>Copy the case code below and submit it to the Canvas assignment. It records
    how you got here.</p>
  `,
};
