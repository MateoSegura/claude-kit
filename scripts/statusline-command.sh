#!/usr/bin/env bash
# Claude Code status line command
# Reads JSON from stdin and outputs a compact status line

input=$(cat)

# --- Model ---
model=$(echo "$input" | jq -r '.model.display_name // "Unknown model"')

# --- Context window ---
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // 0')

# Format context bar
if [ -n "$used_pct" ]; then
  used_int=${used_pct%.*}
  if [ "$used_int" -ge 90 ]; then
    ctx_color="\033[1;31m"   # bold red
  elif [ "$used_int" -ge 75 ]; then
    ctx_color="\033[1;33m"   # bold yellow
  else
    ctx_color="\033[1;32m"   # bold green
  fi
  ctx_str=$(printf "${ctx_color}ctx %.0f%%\033[0m" "$used_pct")
else
  ctx_str="ctx --"
fi

# --- Token counts ---
total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // 0')
total_out=$(echo "$input" | jq -r '.context_window.total_output_tokens // 0')

format_k() {
  local n=$1
  if [ "$n" -ge 1000 ]; then
    printf "%.1fk" "$(echo "scale=1; $n / 1000" | bc)"
  else
    printf "%d" "$n"
  fi
}

in_str=$(format_k "$total_in")
out_str=$(format_k "$total_out")

# --- Current call tokens (if available) ---
cur_in=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // empty')
cur_cache_write=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // 0')
cur_cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // 0')

# --- Session name / ID ---
session_name=$(echo "$input" | jq -r '.session_name // empty')
session_id=$(echo "$input" | jq -r '.session_id // empty')
if [ -n "$session_name" ]; then
  session_str="[$session_name]"
elif [ -n "$session_id" ]; then
  short_id="${session_id:0:8}"
  session_str="[${short_id}]"
else
  session_str=""
fi

# --- Working directory ---
cwd=$(echo "$input" | jq -r '.cwd // empty')
if [ -n "$cwd" ]; then
  # Shorten home directory
  cwd_short="${cwd/#$HOME/~}"
  # If path is long, keep last 2 components
  depth=$(echo "$cwd_short" | tr -cd '/' | wc -c)
  if [ "${#cwd_short}" -gt 40 ]; then
    cwd_short="...$(echo "$cwd_short" | rev | cut -d'/' -f1-2 | rev)"
  fi
fi

# --- Vim mode (optional) ---
vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')
if [ -n "$vim_mode" ]; then
  if [ "$vim_mode" = "INSERT" ]; then
    vim_str="\033[1;34m-- INSERT --\033[0m "
  else
    vim_str="\033[1;33m-- NORMAL --\033[0m "
  fi
else
  vim_str=""
fi

# --- Agent (optional) ---
agent_name=$(echo "$input" | jq -r '.agent.name // empty')
if [ -n "$agent_name" ]; then
  agent_str=" \033[0;35magent:${agent_name}\033[0m"
else
  agent_str=""
fi

# --- Version ---
version=$(echo "$input" | jq -r '.version // empty')
ver_str=""
if [ -n "$version" ]; then
  ver_str=" v${version}"
fi

# --- Assemble ---
# Format:  [session]  model  ctx XX%  in: Xk  out: Xk  ~/path/to/cwd
printf "${vim_str}"
printf "\033[0;36m%s\033[0m  " "$model"
printf "%s  " "$ctx_str"
printf "\033[0;37min:%-5s out:%-5s\033[0m" "$in_str" "$out_str"
if [ -n "$cwd_short" ]; then
  printf "  \033[0;34m%s\033[0m" "$cwd_short"
fi
if [ -n "$session_str" ]; then
  printf "  \033[0;90m%s\033[0m" "$session_str"
fi
printf "%s" "$agent_str"
printf "\n"
