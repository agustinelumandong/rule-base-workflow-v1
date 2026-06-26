#!/usr/bin/env bash
set -euo pipefail

BOOK_DIR="/home/cshan28/Dev/Projects/Experimental/current-workflow/books/longhunter-series/book-2"
REPO="/home/cshan28/Dev/Projects/Experimental/provider-web-driver-mcp"
WORKSPACE="longhunter-series/book-2"
SCRIPTS="/home/cshan28/Dev/Projects/Experimental/current-workflow/.agents/skills/provider-web-chatgpt-chat/scripts"

# Read source files
PHASE0=$(cat "$BOOK_DIR/phase-0.md")
RULEBOOK=$(cat "$BOOK_DIR/rulebook.md")
JAKE=$(cat "$BOOK_DIR/characters/main/jake-moses.md")
CALEB=$(cat "$BOOK_DIR/characters/main/caleb-thorne.md")
RED=$(cat "$BOOK_DIR/characters/antagonists/red-hollow.md")
MCCREA=$(cat "$BOOK_DIR/characters/antagonists/winston-mccrea.md")
BEAR=$(cat "$BOOK_DIR/characters/antagonists/standing-bear.md")
TSALAGI=$(cat "$BOOK_DIR/characters/supporting/tsalagi.md")
ANNA=$(cat "$BOOK_DIR/characters/supporting/anna-ray.md")

generate_chapter() {
  local ch_num=$1
  local ch_name=$2
  local ch_beats=$3
  local target=$4

  local prompt="You are writing Chapter $ch_num: \"$ch_name\" for the novel \"The Long Shadow\" (Longhunter Series Book Two).

## STYLE RULES
- Tight third-person POV from Jake Moses only
- Terse, literal, grounded Western prose
- Dialogue sparse and practical, never decorative
- Character feeling through work, silence, physical behavior, choices only
- No direct inner monologue about guilt, grief, or identity
- Short sentences in action sequences
- No em-dashes
- No modern or clinical vocabulary
- No dialogue tags as stylistic habit
- Literal western action only

## STORY CONTEXT
$PHASE0

## RULEBOOK
$RULEBOOK

## CHARACTERS
### Jake Moses (Protagonist, POV)
$JAKE

### Caleb Thorne (Ally)
$CALEB

### Red Hollow (Antagonist)
$RED

### Winston McCrea (Rival)
$MCCREA

### Standing Bear (Supporting Antagonist)
$BEAR

### Tsalagi (Supporting)
$TSALAGI

### Anna Ray (Supporting)
$ANNA

## CHAPTER $ch_num: $ch_name
**Target:** ~$target words

### Scene Beats
$ch_beats

## INSTRUCTIONS
Write ONLY the prose for Chapter $ch_num. Do not include chapter title, numbering, or any meta-text. Start directly with the opening line of the chapter. Target approximately $target words. Follow all style rules strictly."

  echo "Generating Chapter $ch_num: $ch_name..."
  
  # Build prompt file
  local prompt_file="/tmp/chapter-$ch_num-prompt.txt"
  echo "$prompt" > "$prompt_file"
  
  # Send to ChatGPT
  local response
  response=$(bash "$SCRIPTS/chatgpt_chat.sh" --repo "$REPO" --workspace "$WORKSPACE" --prompt "$(cat "$prompt_file")" --timeout-ms 600000 2>&1)
  
  # Extract response text
  local response_text
  response_text=$(echo "$response" | jq -r '.response_text // empty')
  
  if [[ -z "$response_text" ]]; then
    echo "ERROR: No response for Chapter $ch_num"
    echo "$response"
    return 1
  fi
  
  # Save to file
  echo "$response_text" > "$BOOK_DIR/chapters/chapter-$(printf '%02d' $ch_num).md"
  echo "Saved Chapter $ch_num to chapters/chapter-$(printf '%02d' $ch_num).md"
  
  # Update chapter-summaries.md
  local word_count
  word_count=$(echo "$response_text" | wc -w)
  echo "Chapter $ch_num word count: $word_count"
}

# Chapter definitions
generate_chapter 1 "First Snow" "- Jake checks his cabin and caches. Meat stores are thin. The cabin is solid but the barn is half-finished.
- He scouts the gorge rim. Finds fresh boot prints in the mud, still sharp-edged. At least three men, circling his position within the last two days.
- Jake follows the tracks downstream. Discovers a secondary camp: dead fire, pemmican scraps, a broken tomahawk haft left for repair. Cherokee scouts.
- Among the tracks: boot prints with an uneven right sole. McCrea's gait. Jake recognizes it from the trading post.
- Jake realizes he must abandon the gorge or be surrounded. He has been home for days, not months." "3800"

generate_chapter 2 "Flight Downriver" "- Night exit. Jake packs essential gear: rifle, knife, powder, dried meat, cloak. Leaves heavy tools and cached trade goods behind.
- He enters the river at darkness. The water is low but freezing. He wades through ankle-deep shallows and swims the deeper pools. The cold numbs his legs within minutes.
- The current catches him against submerged timber. He suffers a dislocated shoulder and wrenches it back into place in chest-deep water.
- Dawn finds him on a gravel bar downstream, shivering, shoulder swollen, alone.
- He hears dogs barking upstream. The pursuit has begun." "4000"

generate_chapter 3 "The Trading Post" "- Jake reaches Anna Ray's post, shoulder bound with rawhide. Anna Ray treats the wound without sentiment.
- She tells him: McCrea was here yesterday with three Cherokee men. They bought extra supplies. McCrea said he was guiding them to 'an Indian boy living in a gorge.'
- Anna Ray gives Jake directions to a mountain pass that avoids the main trails. She warns him the pass is narrow and exposed.
- Jake barters for powder and lead. He leaves before dark.
- Jake heads for the pass, knowing the pursuers are behind him." "3900"

generate_chapter 4 "The Pass" "- Jake enters the mountain pass. Narrow walls, loose scree, limited visibility. Bare rock and frost. He finds a camp at the narrow point.
- A Cherokee man named Tsalagi is camped alone. He is a hunter from a different band, traveling independently. He knows Red Hollow by reputation and has no love for him.
- Tsalagi offers a truce: he will guide Jake through the pass if Jake helps him retrieve a horse stolen by McCrea's group.
- Jake agrees reluctantly. They move through the pass together, watching each other.
- They reach the far end of the pass and hear pursuit entering behind them." "4200"

generate_chapter 5 "The Horse" "- Jake and Tsalagi locate the stolen horse, picketed near McCrea's overnight camp. McCrea is alone; the Cherokee scouts are ahead, tracking Jake's river trail.
- They retrieve the horse in darkness. Tsalagi keeps watch while Jake cuts the picket rope.
- McCrea wakes, shouts, fires a pistol. Jake and Tsalagi flee into timber. McCrea does not pursue far.
- Tsalagi confirms McCrea is guiding three warriors: a young leader called Standing Bear, and two others. Red Hollow is not with them yet but is expected.
- They part ways at the ridge fork. Tsalagi goes south with his horse. Jake continues alone toward a defensible position." "4100"

generate_chapter 6 "Standing Bear" "- Jake reaches a narrow defile and decides to set an ambush. He knows the pursuers must pass through.
- Standing Bear and two warriors enter the defile. Jake strikes from above with the tomahawk, wounds Standing Bear in the shoulder. The fight is close and ugly.
- Jake isolates Standing Bear from the other two warriors using terrain. He could kill Standing Bear but chooses to disarm him instead.
- Standing Bear, bleeding, reveals: McCrea has taken Jake's cached trade goods and is heading for the trading post to sell them. Red Hollow is coming with more men.
- Jake lets Standing Bear go with a warning: 'Go home. Do not follow again.'
- Jake knows Red Hollow is coming with a larger force." "4300"

generate_chapter 7 "McCrea" "- Jake reaches the trading post. McCrea is inside, drinking and boasting about killing the 'Indian boy.'
- McCrea has sold Jake's cached goods to a competitor across the river. The goods are gone.
- Jake confronts him. McCrea pulls a knife. The fight happens in the yard, short and brutal.
- Jake kills McCrea but takes a deep cut to his forearm. Anna Ray bandages the wound without comment.
- Jake buries McCrea behind the post. No ceremony.
- Caleb Thorne arrives at the post that evening, drawn by rumors." "4000"

generate_chapter 8 "The Reunion" "- Caleb Thorne arrives. He sees Jake's wound and McCrea's fresh grave. He asks no questions at first.
- Over a fire, they exchange information. Caleb has been in the territory and heard rumors: Red Hollow is coming himself, with six warriors. He plans to reach the gorge and destroy it.
- Jake decides not to run. The gorge is his. He will defend it.
- Caleb agrees to help but warns: 'You hold that gorge alone, you die alone.' Jake accepts the terms.
- They head for the gorge to prepare defenses." "3800"

generate_chapter 9 "The Gorge Defended" "- Jake and Caleb reach the gorge. They reinforce the cabin walls, dig a fighting trench, set deadfall traps on the approach trail.
- They dam the spring to create a mud moat across the narrow entrance.
- Red Hollow arrives with six warriors. They surround the gorge rim. Arrows rain down but the cabin walls hold.
- Jake and Caleb hold the gorge for two days using terrain advantage, limited ammunition, and the narrow approach. Food is already short.
- On the third day, Red Hollow enters the gorge alone, carrying his war axe." "4400"

generate_chapter 10 "The War Chief" "- Red Hollow enters the gorge alone. He wants Jake, not the cabin. This is personal.
- The fight is brutal and close. Tomahawk against knife. Red Hollow is older but experienced. Jake is younger but wounded and weakened from the siege.
- Jake disarms Red Hollow. Breaks his war axe over his knee. Stands over him.
- Jake does not kill Red Hollow. He tells him: 'You came for me. You lost men. You lost McCrea. You lost Standing Bear's loyalty. Take what remains and go.'
- Red Hollow, his authority shaken and his warriors depleted, agrees to withdraw. He leaves with four warriors. Two are dead or deserted.
- Red Hollow departs. The gorge is quiet." "4200"

generate_chapter 11 "Rebuilding" "- Jake and Caleb repair the cabin. The moat is drained, the trench filled, the deadfall cleared.
- Jake restocks his food caches. Caleb teaches him a new drying technique for river fish.
- Jake's forearm wound begins to heal but will scar. He tests his grip on the rifle. It holds.
- Caleb says he will move on. He has his own path. Jake does not ask him to stay.
- Caleb departs at dawn. Jake stands alone in the gorge." "3700"

generate_chapter 12 "The Long Hunt" "- One week later. Jake's forearm is healing. The gorge is restocked. The cabin stands. First snow has fallen.
- He packs for a long hunt. Rifle, knife, tomahawk, cloak, dried meat, powder. He leaves the gorge at dawn.
- He walks into the deep wilderness. No pursuit behind him. No threat waiting.
- The book ends with Jake moving through morning light, alone and unafraid, heading into country no one else has mapped.
- Jake is a Long Hunter. The threats are ended. His home is behind him and the wilderness ahead." "3600"

echo "All chapters generated."