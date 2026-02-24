#!/usr/bin/env bash
# Claude Code status line — dot gauge with rich info
# Reads JSON from stdin, outputs a single compact status line

input=$(cat)

# --- Parse all fields in one jq call ---
eval "$(echo "$input" | jq -r '
  @sh "model=\(.model.display_name // "unknown")",
  @sh "used_pct=\(.context_window.used_percentage // 0)",
  @sh "total_in=\(.context_window.total_input_tokens // 0)",
  @sh "total_out=\(.context_window.total_output_tokens // 0)",
  @sh "cost_usd=\(.cost.total_cost_usd // "")",
  @sh "lines_add=\(.cost.total_lines_added // 0)",
  @sh "lines_rm=\(.cost.total_lines_removed // 0)",
  @sh "vim_mode=\(.vim.mode // "")",
  @sh "agent_name=\(.agent.name // "")"
')"

# --- ANSI colors ---
RST=$'\033[0m'
DIM=$'\033[2m'
BCYAN=$'\033[1;36m'
BGREEN=$'\033[1;32m'
BYELLOW=$'\033[1;33m'
BRED=$'\033[1;31m'
BLUE=$'\033[1;34m'
MAGENTA=$'\033[35m'
WHITE=$'\033[37m'
GRAY=$'\033[90m'

# --- Model (lowercase, bright cyan) ---
model_lower=$(echo "$model" | tr '[:upper:]' '[:lower:]')

# --- Dot gauge: 16 dots, each = 6.25% ---
used_int=${used_pct%.*}
: "${used_int:=0}"

filled=$(( used_int * 16 / 100 ))
[ "$filled" -gt 16 ] && filled=16
empty=$(( 16 - filled ))

# Color tier based on percentage
if [ "$used_int" -ge 90 ]; then
  dot_color="$BRED"
elif [ "$used_int" -ge 75 ]; then
  dot_color="$BYELLOW"
elif [ "$used_int" -ge 50 ]; then
  dot_color="$BGREEN"
else
  dot_color="$BCYAN"
fi

filled_dots=""
for ((i=0; i<filled; i++)); do filled_dots+="●"; done
empty_dots=""
for ((i=0; i<empty; i++)); do empty_dots+="○"; done

# --- Cost ---
if [ -n "$cost_usd" ] && [ "$cost_usd" != "null" ]; then
  cost_fmt=$(printf "%.2f" "$cost_usd")
  cost_cmp=$(awk "BEGIN {if ($cost_usd > 2.0) print \"red\"; else if ($cost_usd > 0.5) print \"yellow\"; else print \"green\"}")
  case "$cost_cmp" in
    red)    cost_color="$BRED" ;;
    yellow) cost_color="$BYELLOW" ;;
    *)      cost_color="$BGREEN" ;;
  esac
  cost_field="${cost_color}\$${cost_fmt}${RST}"
else
  cost_field="${GRAY}--${RST}"
fi

# --- Token formatting (K/M suffix, pure awk) ---
format_tokens() {
  awk "BEGIN {
    n = $1 + 0;
    if (n >= 1000000) printf \"%.1fM\", n / 1000000;
    else if (n >= 1000) printf \"%.0fk\", n / 1000;
    else printf \"%d\", n;
  }"
}

in_str=$(format_tokens "$total_in")
out_str=$(format_tokens "$total_out")

# --- Assemble output ---
# Using %s with pre-built strings avoids printf interpreting \$ as format chars
out=""

# Vim mode (prepend)
if [ -n "$vim_mode" ]; then
  case "$vim_mode" in
    INSERT)  out+="${BLUE}-- INSERT --${RST} " ;;
    NORMAL)  out+="${BLUE}-- NORMAL --${RST} " ;;
    VISUAL)  out+="${BLUE}-- VISUAL --${RST} " ;;
    *)       out+="${BLUE}-- ${vim_mode} --${RST} " ;;
  esac
fi

# Model
out+="${BCYAN}${model_lower}${RST}"

# Dot gauge + percentage
out+="  ${dot_color}${filled_dots}${RST}${GRAY}${empty_dots}${RST}"
out+=" ${dot_color}${used_int}%${RST}"

# Cost
out+="  ${cost_field}"

# Tokens
out+="  ${DIM}${WHITE}↑${in_str} ↓${out_str}${RST}"

# Lines added/removed
out+="  ${BGREEN}+${lines_add}${RST} ${BRED}-${lines_rm}${RST}"

# Agent (append)
if [ -n "$agent_name" ]; then
  out+=" ${MAGENTA}⦿ ${agent_name}${RST}"
fi

printf '%b\n' "$out"
