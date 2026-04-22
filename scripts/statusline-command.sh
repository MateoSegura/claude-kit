#!/usr/bin/env bash
input=$(cat)

eval "$(echo "$input" | jq -r '
  @sh "model=\(.model.display_name // "unknown")",
  @sh "used_pct=\(.context_window.used_percentage // 0)",
  @sh "cache_read=\(.context_window.cache_read_input_tokens // 0)",
  @sh "total_in=\(.context_window.total_input_tokens // 0)",
  @sh "total_out=\(.context_window.total_output_tokens // 0)",
  @sh "cost_usd=\(.cost.total_cost_usd // "")",
  @sh "lines_add=\(.cost.total_lines_added // 0)",
  @sh "lines_rm=\(.cost.total_lines_removed // 0)",
  @sh "duration_ms=\(.cost.total_duration_ms // 0)",
  @sh "rate_5h=\(.rate_limits.five_hour.used_percentage // "")",
  @sh "rate_7d=\(.rate_limits.seven_day.used_percentage // "")",
  @sh "vim_mode=\(.vim.mode // "")",
  @sh "agent_name=\(.agent.name // "")",
  @sh "git_branch=\(.worktree.branch // "")",
  @sh "project_dir=\(.workspace.project_dir // "")"
')"

RST=$'\033[0m'
DIM=$'\033[2m'
ORANGE=$'\033[1;38;5;208m'
BGREEN=$'\033[1;32m'
BYELLOW=$'\033[1;33m'
BRED=$'\033[1;31m'
BLUE=$'\033[1;34m'
BCYAN=$'\033[1;36m'
MAGENTA=$'\033[35m'
WHITE=$'\033[37m'
GRAY=$'\033[90m'

model_lower=$(echo "$model" | tr '[:upper:]' '[:lower:]')

# --- Git info ---
branch=""
if [ -n "$git_branch" ]; then
  branch="$git_branch"
elif [ -n "$project_dir" ] && [ -d "$project_dir/.git" ]; then
  branch=$(git -C "$project_dir" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
fi

repo_name=""
git_dir=""
if [ -n "$project_dir" ]; then
  git_dir=$(git -C "$project_dir" rev-parse --show-toplevel 2>/dev/null || true)
fi
if [ -n "$git_dir" ]; then
  repo_name=$(basename "$git_dir")
fi

dirty=""
git_add=0
git_rm=0
if [ -n "$git_dir" ]; then
  if ! git -C "$git_dir" diff --quiet HEAD 2>/dev/null || [ -n "$(git -C "$git_dir" ls-files --others --exclude-standard 2>/dev/null | head -1)" ]; then
    dirty="x"
  fi
  eval "$(git -C "$git_dir" diff --numstat HEAD 2>/dev/null | awk '{a+=$1; r+=$2} END {printf "git_add=%d\ngit_rm=%d", a, r}')"
fi

# --- Duration ---
dur_sec=$(( duration_ms / 1000 ))
if [ "$dur_sec" -ge 3600 ]; then
  dur_str="$(( dur_sec / 3600 ))h$(( (dur_sec % 3600) / 60 ))m"
elif [ "$dur_sec" -ge 60 ]; then
  dur_str="$(( dur_sec / 60 ))m"
else
  dur_str="${dur_sec}s"
fi

# --- Context dot gauge (16 dots, orange) ---
used_int=${used_pct%.*}
: "${used_int:=0}"
ctx_filled=$(( used_int * 16 / 100 ))
[ "$ctx_filled" -gt 16 ] && ctx_filled=16
ctx_empty=$(( 16 - ctx_filled ))

ctx_filled_dots=""
for ((i=0; i<ctx_filled; i++)); do ctx_filled_dots+="●"; done
ctx_empty_dots=""
for ((i=0; i<ctx_empty; i++)); do ctx_empty_dots+="○"; done

# --- Cost ---
if [ -n "$cost_usd" ] && [ "$cost_usd" != "null" ]; then
  cost_fmt=$(printf "%.2f" "$cost_usd")
  cost_cmp=$(awk "BEGIN {if ($cost_usd > 100.0) print \"red\"; else if ($cost_usd > 50.0) print \"yellow\"; else print \"green\"}")
  case "$cost_cmp" in
    red)    cost_color="$BRED" ;;
    yellow) cost_color="$BYELLOW" ;;
    *)      cost_color="$BGREEN" ;;
  esac
  cost_field="${cost_color}\$${cost_fmt}${RST}"
else
  cost_field="${GRAY}--${RST}"
fi

# --- Token formatting ---
fmt_tok() {
  awk "BEGIN {
    n = $1 + 0;
    if (n >= 1000000) printf \"%.1fM\", n / 1000000;
    else if (n >= 1000) printf \"%.0fk\", n / 1000;
    else printf \"%d\", n;
  }"
}

in_str=$(fmt_tok "$total_in")
out_str=$(fmt_tok "$total_out")

# --- Usage bar (5h subscription window, 16 dots, cyan/green/yellow/red) ---
usage_field=""
if [ -n "$rate_5h" ] && [ "$rate_5h" != "null" ]; then
  rate_int=${rate_5h%.*}
  : "${rate_int:=0}"
  u_filled=$(( rate_int * 16 / 100 ))
  [ "$u_filled" -gt 16 ] && u_filled=16
  u_empty=$(( 16 - u_filled ))

  if [ "$rate_int" -ge 90 ]; then u_color="$BRED"
  elif [ "$rate_int" -ge 75 ]; then u_color="$BYELLOW"
  elif [ "$rate_int" -ge 50 ]; then u_color="$BGREEN"
  else u_color="$BCYAN"
  fi

  u_filled_str=""
  for ((i=0; i<u_filled; i++)); do u_filled_str+="●"; done
  u_empty_str=""
  for ((i=0; i<u_empty; i++)); do u_empty_str+="○"; done

  weekly=""
  if [ -n "$rate_7d" ] && [ "$rate_7d" != "null" ]; then
    week_int=${rate_7d%.*}
    : "${week_int:=0}"
    if [ "$week_int" -ge 90 ]; then w_color="$BRED"
    elif [ "$week_int" -ge 75 ]; then w_color="$BYELLOW"
    elif [ "$week_int" -ge 50 ]; then w_color="$BGREEN"
    else w_color="$BCYAN"
    fi
    weekly="${GRAY}/${RST}${w_color}${week_int}%${RST}"
  fi

  usage_field="${u_color}${u_filled_str}${RST}${GRAY}${u_empty_str}${RST} ${u_color}${rate_int}%${RST}${weekly}"
fi

# --- Assemble ---
out=""

if [ -n "$vim_mode" ]; then
  case "$vim_mode" in
    INSERT)  out+="${BLUE}-- INSERT --${RST} " ;;
    NORMAL)  out+="${BLUE}-- NORMAL --${RST} " ;;
    VISUAL)  out+="${BLUE}-- VISUAL --${RST} " ;;
    *)       out+="${BLUE}-- ${vim_mode} --${RST} " ;;
  esac
fi

if [ -n "$repo_name" ]; then
  out+="${BCYAN}${repo_name}${RST}"
  if [ -n "$branch" ]; then
    out+=" ${GRAY}on${RST} ${MAGENTA}${branch}${RST}"
  fi
  if [ -n "$dirty" ]; then
    out+=" ${BRED}x${RST}"
  else
    out+=" ${BGREEN}✓${RST}"
  fi
  out+=" ${BGREEN}+${git_add}${RST} ${BRED}-${git_rm}${RST}"
  out+=" ${GRAY}-${RST} "
fi

out+="${ORANGE}${model_lower}${RST}"

out+="  ${ORANGE}${ctx_filled_dots}${RST}${GRAY}${ctx_empty_dots}${RST}"
cache_pct=0
if [ "$total_in" -gt 0 ]; then
  cache_pct=$(( cache_read * 100 / total_in ))
fi
if [ "$cache_pct" -ge 70 ]; then cache_color="$BGREEN"
elif [ "$cache_pct" -ge 40 ]; then cache_color="$BYELLOW"
else cache_color="$BRED"
fi
out+=" ${ORANGE}${used_int}%${RST} ${cache_color}(${cache_pct}%c)${RST}"

out+="  ${cost_field}"

out+="  ${DIM}${WHITE}↑${in_str} ↓${out_str}${RST}"

if [ -n "$usage_field" ]; then
  out+="  ${GRAY}-${RST} ${usage_field}"
else
  out+="  ${GRAY}-${RST} ${GRAY}○○○○○○○○○○○○○○○○ --%/--%${RST}"
fi
out+=" ${GRAY}-${RST} ${GRAY}duration: ${dur_str}${RST}"

if [ -n "$agent_name" ]; then
  out+="  ${MAGENTA}${agent_name}${RST}"
fi

printf '%b\n' "$out"
