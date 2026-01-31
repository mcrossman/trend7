library(shiny)
library(tidyverse)
library(claudeR)
library(plotly)

# Load data at startup
trends_url <- "https://docs.google.com/spreadsheets/d/e/2PACX-1vSrKHb7GBESctOrTm64jO45E_yXP-2mkRkZwA4iJ1ODLzNBeZ-1Wq3Sbp2mgWIYi9DWW_rDm_J63qTo/pub?output=csv"
atlantic_url <- "https://docs.google.com/spreadsheets/d/e/2PACX-1vSewjiUQLcD9thwGowZUPoLO_D9bNhRvTQkH4M7mOhs4wnvsjqtXLwcUxdddn2nii4bIoNcGQ0-7hsK/pub?gid=886238778&single=true&output=csv"

trends_data <- read_csv(trends_url, show_col_types = FALSE) |>
  mutate(
    increase_numeric = suppressWarnings(as.numeric(increase_percent)),
    is_breakout = increase_percent == "Breakout",
    is_high = !is.na(increase_numeric) & increase_numeric > 1000
  ) |>
  filter(is_breakout | is_high)

atlantic_data <- read_csv(atlantic_url, show_col_types = FALSE) |>
  mutate(date_published = as.Date(date_published))

ui <- fluidPage(
  tags$head(
    # Load Lucide icons
    tags$script(src = "https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"),
    tags$style(HTML("
      body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #f5f5f5;
        padding: 20px;
      }
      .main-container {
        max-width: 1200px;
        margin: 0 auto;
      }
      .header {
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid #e0e0e0;
      }
      .logo-icon {
        width: 28px;
        height: 28px;
        flex-shrink: 0;
      }
      h1 { 
        font-weight: 600; 
        margin-bottom: 4px;
        color: #1a1a1a;
        font-size: 24px;
        display: flex;
        align-items: center;
        gap: 10px;
      }
      h3 {
        font-weight: 400;
        font-size: 16px;
        color: #444;
        margin-top: 0;
        margin-bottom: 8px;
      }
      .subtitle {
        color: #666;
        font-size: 14px;
        line-height: 1.5;
        max-width: 700px;
      }
      .trends-panel {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        height: fit-content;
        position: sticky;
        top: 20px;
      }
      .panel-title {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .group-title {
        font-size: 12px;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        margin-top: 20px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .group-title:first-child {
        margin-top: 0;
      }
      .group-title svg {
        width: 14px;
        height: 14px;
      }
      .trend-item {
        padding: 10px 12px;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 4px;
        transition: all 0.15s;
        font-size: 14px;
        border: 1px solid transparent;
      }
      .trend-item:hover {
        background: #f5f5f5;
        border-color: #e0e0e0;
      }
      .trend-item.selected {
        background: #1a1a1a;
        color: white;
        border-color: #1a1a1a;
      }
      .trend-meta {
        font-size: 11px;
        color: #999;
        margin-top: 2px;
      }
      .trend-item.selected .trend-meta {
        color: #888;
      }
      .results-container {
        background: white;
        padding: 28px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
      }
      .section-title {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .section-title svg {
        width: 14px;
        height: 14px;
      }
      .article-card {
        padding: 16px 20px;
        border-radius: 6px;
        margin-bottom: 10px;
        border-left: 3px solid #333;
        background: #fafafa;
      }
      .article-title {
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 6px;
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }
      .article-title-text {
        flex: 1;
        line-height: 1.4;
      }
      .article-meta {
        font-size: 12px;
        color: #888;
      }
      .article-excerpt {
        font-size: 13px;
        color: #555;
        margin-top: 10px;
        line-height: 1.6;
      }
      .section-tag {
        display: inline-block;
        background: #e8e8e8;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 11px;
        color: #555;
        margin-right: 8px;
      }
      .reasoning-box {
        background: #f8f8f8;
        border-radius: 6px;
        padding: 16px;
        margin-bottom: 24px;
        font-size: 14px;
        color: #444;
        line-height: 1.6;
      }
      .reasoning-label {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .reasoning-label svg {
        width: 14px;
        height: 14px;
      }
      .story-pitch {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 8px;
        padding: 24px;
        margin-bottom: 28px;
      }
      .story-pitch-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
      }
      .story-pitch-header svg {
        width: 18px;
        height: 18px;
        color: #b45309;
      }
      .story-pitch-label {
        font-size: 11px;
        font-weight: 700;
        color: #b45309;
        text-transform: uppercase;
        letter-spacing: 1px;
      }
      .story-pitch-content {
        font-size: 14px;
        color: #374151;
        line-height: 1.7;
      }
      .story-pitch-content ul {
        margin: 0;
        padding-left: 20px;
      }
      .story-pitch-content li {
        margin-bottom: 10px;
      }
      .story-pitch-content li:last-child {
        margin-bottom: 0;
      }
      .score-badge {
        display: inline-block;
        background: #e5e5e5;
        color: #555;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        flex-shrink: 0;
        white-space: nowrap;
      }
      .score-high {
        background: #dcfce7;
        color: #166534;
      }
      .score-medium {
        background: #fef3c7;
        color: #92400e;
      }
      .score-low {
        background: #f1f5f9;
        color: #64748b;
      }
      .trend-info {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 24px;
      }
      .trend-query {
        font-size: 20px;
        font-weight: 600;
        color: #1a1a1a;
      }
      .trend-info-meta {
        font-size: 13px;
        color: #666;
        margin-top: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .trend-info-meta svg {
        width: 14px;
        height: 14px;
      }
      .stats-row {
        display: flex;
        gap: 12px;
        margin-bottom: 20px;
      }
      .stat-box {
        flex: 1;
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 12px 16px;
        text-align: center;
      }
      .stat-number {
        font-size: 24px;
        font-weight: 600;
        color: #1a1a1a;
      }
      .stat-label {
        font-size: 11px;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 2px;
      }
      .mini-chart {
        background: #fafafa;
        border: 1px solid #e5e5e5;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 20px;
      }
      .mini-chart-title {
        font-size: 11px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .mini-chart-title svg {
        width: 14px;
        height: 14px;
      }
      .mini-chart .plotly {
        height: 100px !important;
      }
      .loading {
        text-align: center;
        padding: 60px 20px;
        color: #666;
      }
      .loading-icon {
        margin-bottom: 15px;
      }
      .loading-icon svg {
        width: 32px;
        height: 32px;
        animation: spin 1.5s linear infinite;
        color: #888;
      }
      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      .empty-state {
        text-align: center;
        padding: 80px 20px;
        color: #888;
      }
      .empty-state-icon {
        margin-bottom: 15px;
      }
      .empty-state-icon svg {
        width: 48px;
        height: 48px;
        color: #ccc;
      }
      .empty-state-text {
        font-size: 15px;
      }
      .initial-loading {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 60px 20px;
        color: #666;
      }
      .initial-loading .spinner {
        width: 32px;
        height: 32px;
        border: 3px solid #e5e5e5;
        border-top-color: #333;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-bottom: 16px;
      }
    "))
  ),
  
  div(class = "main-container",
      div(class = "header",
          h1(
            HTML('<svg class="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path opacity="0.5" d="M19 22V21.5M5 22V21.5" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M12 21V2" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path opacity="0.5" d="M15 8V10" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M2 10C2 6.22876 2 4.34315 3.17157 3.17157C4.34315 2 6.22876 2 10 2H14C17.7712 2 19.6569 2 20.8284 3.17157C22 4.34315 22 6.22876 22 10V13C22 16.7712 22 18.6569 20.8284 19.8284C19.6569 21 17.7712 21 14 21H10C6.22876 21 4.34315 21 3.17157 19.8284C2 18.6569 2 16.7712 2 13V10Z" stroke="#1C274C" stroke-width="1.5"/>
          <path opacity="0.5" d="M2 8H12" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path d="M2 15H22" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path opacity="0.5" d="M15 18L17 18" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
          <path opacity="0.5" d="M7 18L9 18" stroke="#1C274C" stroke-width="1.5" stroke-linecap="round"/>
        </svg>'),
            "TrendCloset"
          ),
          h3("Find the story that meets the moment"),
          p(class = "subtitle", "TrendCloset monitors emerging trends and surfaces relevant archive content — so you can reshare valuable journalism at the perfect moment and give reporters the context they need to write new stories.")
      ),
      
      fluidRow(
        column(3,
               div(class = "trends-panel",
                   div(class = "panel-title", 
                       tags$i(`data-lucide` = "trending-up"),
                       "Trending Now"
                   ),
                   uiOutput("trends_list")
               )
        ),
        column(9,
               uiOutput("results")
        )
      )
  ),
  
  # Initialize Lucide icons
  tags$script(HTML("
    $(document).ready(function() {
      lucide.createIcons();
    });
    $(document).on('shiny:value', function(event) {
      setTimeout(function() { lucide.createIcons(); }, 100);
    });
  "))
)

server <- function(input, output, session) {
  
  # Store results
  results <- reactiveValues(
    trend = NULL,
    articles = NULL,
    scores = NULL,
    reasoning = NULL,
    story_pitch = NULL,
    selected_query = NULL
  )
  
  # Render trends list grouped by breakout vs high growth
  output$trends_list <- renderUI({
    breakouts <- trends_data |> filter(is_breakout)
    high_growth <- trends_data |> filter(is_high & !is_breakout)
    
    make_trend_items <- function(df) {
      map(seq_len(nrow(df)), function(i) {
        row <- df[i, ]
        is_selected <- !is.null(results$selected_query) && results$selected_query == row$query
        
        div(
          class = paste("trend-item", if (is_selected) "selected" else ""),
          onclick = sprintf("Shiny.setInputValue('clicked_trend', '%s', {priority: 'event'})", row$query),
          row$query,
          div(class = "trend-meta", paste0(row$month, "/", row$year))
        )
      })
    }
    
    tagList(
      if (nrow(breakouts) > 0) tagList(
        div(class = "group-title", 
            tags$i(`data-lucide` = "flame"),
            "Breakout"
        ),
        make_trend_items(breakouts)
      ),
      if (nrow(high_growth) > 0) tagList(
        div(class = "group-title", 
            tags$i(`data-lucide` = "trending-up"),
            "High Growth"
        ),
        make_trend_items(high_growth)
      )
    )
  })
  
  # Handle trend click
  observeEvent(input$clicked_trend, {
    selected_query <- input$clicked_trend
    results$selected_query <- selected_query
    
    # Get selected trend info
    trend_info <- trends_data |> filter(query == selected_query)
    results$trend <- trend_info
    
    # Show loading
    results$articles <- NULL
    results$scores <- NULL
    results$reasoning <- "Loading..."
    results$story_pitch <- NULL
    
    # Build list of Atlantic titles with IDs, sections, and topics
    titles_list <- atlantic_data |>
      mutate(
        section_info = if_else(is.na(site_section), "", paste0(" [", site_section, "]")),
        topic_info = if_else(is.na(topic_name), "", paste0(" {", topic_name, "}")),
        item = paste0("[", row_number(), "] ", title, section_info, topic_info)
      ) |>
      pull(item) |>
      paste(collapse = "\n")
    
    # Get recent and key archive pieces for context
    recent_articles <- atlantic_data |>
      arrange(desc(date_published)) |>
      slice_head(n = 5) |>
      mutate(ref = paste0(title, " (", date_published, ")")) |>
      pull(ref) |>
      paste(collapse = "; ")
    
    # Build prompt
    prompt_text <- paste0(
      "You are helping match trending Google searches to relevant journalism from The Atlantic's archive.\n\n",
      "TRENDING TOPIC: ", selected_query, "\n",
      "Context: This was a '", trend_info$increase_percent, "' trending topic in ", 
      trend_info$month, "/", trend_info$year, ".\n\n",
      "Below is a list of Atlantic article titles with IDs, [sections], and {topics}.\n",
      "Select the 5-10 most relevant articles that would help someone understand this trending topic.\n",
      "Consider articles that provide context, analysis, background, or related perspectives.\n",
      "Use the section and topic metadata to help identify relevant content.\n\n",
      "ARTICLE TITLES:\n", titles_list, "\n\n",
      "RESPOND IN THIS EXACT FORMAT (no extra text):\n",
      "REASONING: [1-2 sentences explaining your selection logic]\n",
      "SELECTED: [comma-separated list of article IDs with scores, e.g., 42:95, 156:82, 789:71 - where the number after : is a relevance score from 1-100]\n\n",
      "---\n\n",
      "Now, as a seasoned Atlantic editor known for identifying compelling story angles that blend timeliness, depth, and cultural resonance, generate a story pitch based on this trend and the archive coverage you selected.\n\n",
      "CONTEXT:\n",
      "- Emerging trend: ", selected_query, "\n",
      "- Our archive contains articles from 2025\n",
      "- Recent coverage: ", recent_articles, "\n\n",
      "Your pitch must:\n",
      "1. IDENTIFY A SPECIFIC ANGLE that goes beyond surface reporting - not just 'update the numbers' but find the counterintuitive, the human stakes, or the larger pattern\n",
      "2. SHOW ATLANTIC READER RESONANCE - depth over speed, context over facts, ideas/systems/power/human experience\n",
      "3. BUILD ON INSTITUTIONAL KNOWLEDGE - reference past coverage, show how this advances/complicates our reporting\n\n",
      "AVOID: Generic importance claims, pitches any outlet could write, 'it's trending' as sole justification, ignoring archive, just updating numbers\n\n",
      "FORMAT:\n",
      "PITCHES:\n",
      "- [First story idea as single sentence with specific angle, why now, Atlantic style]\n",
      "- [Second story idea]\n",
      "- [Third story idea]\n\n",
      "Max 60 words total for all three. Be specific, not generic."
    )
    
    # Call Claude
    tryCatch({
      response <- claudeR(
        prompt = list(list(role = "user", content = prompt_text)),
        model = "claude-sonnet-4-20250514",
        max_tokens = 1200
      )
      
      # Parse response - updated regex for new format (no HEADLINE)
      reasoning_match <- str_match(response, "REASONING:\\s*(.+?)\\s*SELECTED:")
      selected_match <- str_match(response, "SELECTED:\\s*([0-9:,\\s]+?)\\s*---")
      
      # If no --- delimiter, try to match until PITCHES
      if (is.na(selected_match[1, 2])) {
        selected_match <- str_match(response, "SELECTED:\\s*([0-9:,\\s]+?)\\s*PITCHES:")
      }
      # If still no match, try looser pattern
      if (is.na(selected_match[1, 2])) {
        selected_match <- str_match(response, "SELECTED:\\s*([0-9:,\\s]+)")
      }
      
      pitch_match <- str_match(response, "(?s)PITCHES:\\s*(.+)$")
      
      if (!is.na(reasoning_match[1, 2])) {
        results$reasoning <- str_trim(reasoning_match[1, 2])
      } else {
        results$reasoning <- NULL
      }
      
      if (!is.na(pitch_match[1, 2])) {
        results$story_pitch <- str_trim(pitch_match[1, 2])
      } else {
        results$story_pitch <- NULL
      }
      
      if (!is.na(selected_match[1, 2])) {
        # Parse ID:score pairs
        pairs <- selected_match[1, 2] |>
          str_split(",") |>
          unlist() |>
          str_trim()
        
        ids <- c()
        scores <- c()
        
        for (pair in pairs) {
          parts <- str_split(pair, ":")[[1]]
          if (length(parts) == 2) {
            ids <- c(ids, as.integer(parts[1]))
            scores <- c(scores, as.integer(parts[2]))
          } else if (length(parts) == 1 && nchar(parts[1]) > 0) {
            ids <- c(ids, as.integer(parts[1]))
            scores <- c(scores, NA)
          }
        }
        
        if (length(ids) > 0) {
          results$scores <- scores
          results$articles <- atlantic_data |>
            slice(ids) |>
            mutate(relevance_score = scores) |>
            filter(!is.na(title)) |>
            arrange(desc(relevance_score))
        } else {
          results$articles <- NULL
          results$scores <- NULL
        }
      } else {
        results$articles <- NULL
        results$scores <- NULL
      }
      
    }, error = function(e) {
      results$reasoning <- paste("Error:", e$message)
      results$articles <- NULL
      results$scores <- NULL
      results$story_pitch <- NULL
    })
  })
  
  output$results <- renderUI({
    if (is.null(results$trend)) {
      return(
        div(class = "results-container",
            div(class = "empty-state",
                div(class = "empty-state-icon", 
                    tags$i(`data-lucide` = "mouse-pointer-click")
                ),
                div(class = "empty-state-text", "Select a trending topic to discover relevant articles")
            )
        )
      )
    }
    
    trend <- results$trend
    
    trend_box <- div(class = "trend-info",
                     div(class = "trend-query", trend$query),
                     div(class = "trend-info-meta", 
                         tags$i(`data-lucide` = "trending-up"),
                         paste0(trend$increase_percent, " increase  /  ", trend$month, "/", trend$year)
                     )
    )
    
    if (is.null(results$articles) && !is.null(results$reasoning) && results$reasoning == "Loading...") {
      return(
        div(class = "results-container",
            trend_box,
            div(class = "initial-loading",
                div(class = "spinner"),
                div("Analyzing archive for relevant stories...")
            )
        )
      )
    }
    
    # Reasoning box
    reasoning_box <- if (!is.null(results$reasoning) && nchar(results$reasoning) > 0) {
      div(class = "reasoning-box",
          div(class = "reasoning-label",
              tags$i(`data-lucide` = "sparkles"),
              "Selection Logic"
          ),
          results$reasoning
      )
    } else {
      NULL
    }
    
    # Story pitch box - parse bullets into list
    story_box <- if (!is.null(results$story_pitch) && nchar(results$story_pitch) > 0) {
      # Parse bullet points
      bullets <- results$story_pitch |>
        str_split("\\n-|^-") |>
        unlist() |>
        str_trim() |>
        discard(~ nchar(.x) == 0)
      
      div(class = "story-pitch",
          div(class = "story-pitch-header",
              tags$i(`data-lucide` = "lightbulb"),
              span(class = "story-pitch-label", "Story Ideas")
          ),
          div(class = "story-pitch-content",
              tags$ul(
                map(bullets, ~ tags$li(.x))
              )
          )
      )
    } else {
      NULL
    }
    
    if (is.null(results$articles) || nrow(results$articles) == 0) {
      return(
        div(class = "results-container",
            trend_box,
            story_box,
            reasoning_box,
            p("No relevant articles found in the archive.")
        )
      )
    }
    
    # Calculate stats
    n_articles <- nrow(results$articles)
    avg_score <- round(mean(results$articles$relevance_score, na.rm = TRUE))
    
    # Get date range of matched articles
    date_range <- results$articles |>
      summarise(
        min_date = min(date_published, na.rm = TRUE),
        max_date = max(date_published, na.rm = TRUE)
      )
    
    # Articles by month for mini chart
    articles_by_month <- results$articles |>
      mutate(month = floor_date(date_published, "month")) |>
      count(month) |>
      arrange(month)
    
    # Stats row
    stats_box <- div(class = "stats-row",
                     div(class = "stat-box",
                         div(class = "stat-number", n_articles),
                         div(class = "stat-label", "Matches")
                     ),
                     div(class = "stat-box",
                         div(class = "stat-number", paste0(avg_score, "%")),
                         div(class = "stat-label", "Avg Relevance")
                     ),
                     div(class = "stat-box",
                         div(class = "stat-number", format(date_range$min_date, "%b %Y")),
                         div(class = "stat-label", "Earliest")
                     ),
                     div(class = "stat-box",
                         div(class = "stat-number", format(date_range$max_date, "%b %Y")),
                         div(class = "stat-label", "Latest")
                     )
    )
    
    # Mini chart
    chart_box <- if (nrow(articles_by_month) > 1) {
      p <- plot_ly(articles_by_month, x = ~month, y = ~n, type = "bar",
                   marker = list(color = "#333")) |>
        layout(
          xaxis = list(title = "", tickfont = list(size = 10)),
          yaxis = list(title = "", tickfont = list(size = 10)),
          margin = list(l = 25, r = 10, t = 5, b = 25),
          height = 80
        ) |>
        config(displayModeBar = FALSE)
      
      div(class = "mini-chart",
          div(class = "mini-chart-title",
              tags$i(`data-lucide` = "bar-chart-2"),
              "Coverage Over Time"
          ),
          p
      )
    } else {
      NULL
    }
    
    article_cards <- map(seq_len(nrow(results$articles)), function(i) {
      row <- results$articles[i, ]
      pub_date <- as.character(row$date_published)
      excerpt <- if (!is.na(row$content) && nchar(row$content) > 200) {
        paste0(substr(row$content, 1, 200), "...")
      } else {
        row$content
      }
      
      # Determine score class
      score <- row$relevance_score
      score_class <- if (is.na(score)) {
        "score-badge"
      } else if (score >= 80) {
        "score-badge score-high"
      } else if (score >= 50) {
        "score-badge score-medium"
      } else {
        "score-badge score-low"
      }
      
      div(class = "article-card",
          div(class = "article-title", 
              span(class = "article-title-text", row$title),
              if (!is.na(score)) span(class = score_class, paste0(score, "% match"))
          ),
          div(class = "article-meta",
              if (!is.na(row$site_section)) span(class = "section-tag", row$site_section),
              paste(row$byline, " / ", pub_date)
          ),
          if (!is.na(excerpt)) div(class = "article-excerpt", excerpt)
      )
    })
    
    div(class = "results-container",
        trend_box,
        stats_box,
        chart_box,
        story_box,
        reasoning_box,
        div(class = "section-title", 
            tags$i(`data-lucide` = "files"),
            paste0("Archive Matches (", nrow(results$articles), " articles)")
        ),
        tagList(article_cards)
    )
  })
}

shinyApp(ui, server)