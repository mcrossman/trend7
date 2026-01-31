library(shiny)
library(tidyverse)
library(claudeR)

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
    tags$style(HTML("
      body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        background: #fafafa;
        padding: 20px;
      }
      .main-container {
        max-width: 1200px;
        margin: 0 auto;
      }
      .header {
        margin-bottom: 30px;
        padding-bottom: 20px;
        border-bottom: 1px solid #eee;
      }
      h1 { 
        font-weight: 600; 
        margin-bottom: 8px;
        color: #1a1a1a;
        font-size: 28px;
      }
      .subtitle {
        color: #666;
        font-size: 15px;
        line-height: 1.5;
        max-width: 700px;
      }
      .trends-panel {
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        height: fit-content;
        position: sticky;
        top: 20px;
      }
      .panel-title {
        font-size: 12px;
        font-weight: 600;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 15px;
      }
      .group-title {
        font-size: 13px;
        font-weight: 600;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
        margin-top: 20px;
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .group-title:first-child {
        margin-top: 0;
      }
      .trend-item {
        padding: 10px 12px;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 5px;
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
        color: #888;
        margin-top: 2px;
      }
      .trend-item.selected .trend-meta {
        color: #aaa;
      }
      .results-container {
        background: white;
        padding: 25px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      }
      .section-title {
        font-size: 12px;
        font-weight: 600;
        color: #888;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .article-card {
        padding: 15px 20px;
        border-radius: 6px;
        margin-bottom: 10px;
        border-left: 3px solid #0066cc;
        background: #f9f9f9;
      }
      .article-title {
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 5px;
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
      }
      .article-meta {
        font-size: 12px;
        color: #888;
      }
      .article-excerpt {
        font-size: 13px;
        color: #555;
        margin-top: 8px;
        line-height: 1.5;
      }
      .section-tag {
        display: inline-block;
        background: #e0e0e0;
        padding: 2px 8px;
        border-radius: 3px;
        font-size: 11px;
        color: #666;
        margin-right: 5px;
      }
      .claude-reasoning {
        background: #f8f9fa;
        border-left: 3px solid #6c757d;
        padding: 15px;
        margin-bottom: 20px;
        font-size: 14px;
        color: #333;
        line-height: 1.6;
      }
      .story-idea {
        background: linear-gradient(135deg, #f0fff4 0%, #e6ffed 100%);
        border: 1px solid #86efac;
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 25px;
      }
      .story-idea-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
      }
      .story-idea-icon {
        font-size: 20px;
      }
      .story-idea-label {
        font-size: 12px;
        font-weight: 600;
        color: #16a34a;
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
      .story-idea-headline {
        font-size: 18px;
        font-weight: 600;
        color: #1a1a1a;
        margin-bottom: 10px;
        line-height: 1.3;
      }
      .story-idea-pitch {
        font-size: 14px;
        color: #444;
        line-height: 1.6;
      }
      .score-badge {
        display: inline-block;
        background: #0066cc;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: 600;
        flex-shrink: 0;
      }
      .score-high {
        background: #22c55e;
      }
      .score-medium {
        background: #f59e0b;
      }
      .score-low {
        background: #94a3b8;
      }
      .trend-info {
        background: linear-gradient(135deg, #fff8e6 0%, #fef3c7 100%);
        border: 1px solid #fcd34d;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 20px;
      }
      .trend-query {
        font-size: 22px;
        font-weight: 600;
        color: #1a1a1a;
      }
      .trend-info-meta {
        font-size: 13px;
        color: #666;
        margin-top: 5px;
      }
      .loading {
        text-align: center;
        padding: 60px 20px;
        color: #666;
      }
      .loading-spinner {
        font-size: 32px;
        margin-bottom: 15px;
        animation: pulse 1.5s ease-in-out infinite;
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      .empty-state {
        text-align: center;
        padding: 80px 20px;
        color: #888;
      }
      .empty-state-icon {
        font-size: 48px;
        margin-bottom: 15px;
      }
      .empty-state-text {
        font-size: 15px;
      }
    "))
  ),
  
  div(class = "main-container",
      div(class = "header",
          h1("\U0001F4C8 Trends \U2192 The Atlantic"),
          p(class = "subtitle", "Monitors emerging trends and surfaces relevant archive content — so you can reshare valuable journalism at the perfect moment and give reporters the context they need to write new stories.")
      ),
      
      fluidRow(
        column(3,
               div(class = "trends-panel",
                   div(class = "panel-title", "Trending Now"),
                   uiOutput("trends_list")
               )
        ),
        column(9,
               uiOutput("results")
        )
      )
  )
)

server <- function(input, output, session) {
  
  # Store results
  results <- reactiveValues(
    trend = NULL,
    articles = NULL,
    scores = NULL,
    reasoning = NULL,
    story_headline = NULL,
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
        div(class = "group-title", "\U0001F525 Breakout"),
        make_trend_items(breakouts)
      ),
      if (nrow(high_growth) > 0) tagList(
        div(class = "group-title", "\U0001F4C8 High Growth"),
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
    results$story_headline <- NULL
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
      "SELECTED: [comma-separated list of article IDs with scores, e.g., 42:95, 156:82, 789:71 - where the number after : is a relevance score from 1-100]\n",
      "HEADLINE: [A compelling Atlantic-style headline for a new article about this trend]\n",
      "PITCH: [2-3 sentence pitch explaining the angle, why it matters now, and why it would resonate with Atlantic readers]"
    )
    
    # Call Claude
    tryCatch({
      response <- claudeR(
        prompt = list(list(role = "user", content = prompt_text)),
        model = "claude-sonnet-4-20250514",
        max_tokens = 800
      )
      
      # Parse response
      reasoning_match <- str_match(response, "REASONING:\\s*(.+?)\\s*SELECTED:")
      selected_match <- str_match(response, "SELECTED:\\s*([0-9:,\\s]+?)\\s*HEADLINE:")
      headline_match <- str_match(response, "HEADLINE:\\s*(.+?)\\s*PITCH:")
      pitch_match <- str_match(response, "PITCH:\\s*(.+)$")
      
      if (!is.na(reasoning_match[1, 2])) {
        results$reasoning <- str_trim(reasoning_match[1, 2])
      } else {
        results$reasoning <- "Claude suggested the following articles:"
      }
      
      if (!is.na(headline_match[1, 2])) {
        results$story_headline <- str_trim(headline_match[1, 2])
      } else {
        results$story_headline <- NULL
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
          } else {
            ids <- c(ids, as.integer(parts[1]))
            scores <- c(scores, NA)
          }
        }
        
        results$scores <- scores
        results$articles <- atlantic_data |>
          slice(ids) |>
          mutate(relevance_score = scores) |>
          filter(!is.na(title)) |>
          arrange(desc(relevance_score))
      } else {
        results$reasoning <- paste("Could not parse response:", response)
        results$articles <- NULL
        results$scores <- NULL
      }
      
    }, error = function(e) {
      results$reasoning <- paste("Error calling Claude:", e$message)
      results$articles <- NULL
      results$scores <- NULL
      results$story_headline <- NULL
      results$story_pitch <- NULL
    })
  })
  
  output$results <- renderUI({
    if (is.null(results$trend)) {
      return(
        div(class = "results-container",
            div(class = "empty-state",
                div(class = "empty-state-icon", "\U0001F448"),
                div(class = "empty-state-text", "Select a trending topic to discover relevant articles")
            )
        )
      )
    }
    
    trend <- results$trend
    
    trend_box <- div(class = "trend-info",
                     div(class = "trend-query", trend$query),
                     div(class = "trend-info-meta", 
                         paste0("\U0001F4C8 ", trend$increase_percent, " increase \U2022 ", trend$month, "/", trend$year))
    )
    
    if (is.null(results$articles) && results$reasoning == "Loading...") {
      return(
        div(class = "results-container",
            trend_box,
            div(class = "loading",
                div(class = "loading-spinner", "\U0001F50D"),
                div("Analyzing archive for relevant stories...")
            )
        )
      )
    }
    
    reasoning_box <- div(class = "claude-reasoning", 
                         tags$strong("Why these articles: "), results$reasoning
    )
    
    if (is.null(results$articles) || nrow(results$articles) == 0) {
      return(
        div(class = "results-container",
            trend_box,
            reasoning_box,
            p("No relevant articles found in the archive.")
        )
      )
    }
    
    # Story idea box
    story_box <- if (!is.null(results$story_headline) && !is.null(results$story_pitch)) {
      div(class = "story-idea",
          div(class = "story-idea-header",
              span(class = "story-idea-icon", "\U0001F4A1"),
              span(class = "story-idea-label", "New Story Opportunity")
          ),
          div(class = "story-idea-headline", results$story_headline),
          div(class = "story-idea-pitch", results$story_pitch)
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
              span(row$title),
              if (!is.na(score)) span(class = score_class, paste0(score, "% match"))
          ),
          div(class = "article-meta",
              if (!is.na(row$site_section)) span(class = "section-tag", row$site_section),
              paste(row$byline, "\U2022", pub_date)
          ),
          if (!is.na(excerpt)) div(class = "article-excerpt", excerpt)
      )
    })
    
    div(class = "results-container",
        trend_box,
        story_box,
        reasoning_box,
        div(class = "section-title", paste0("Archive Matches (", nrow(results$articles), " articles)")),
        tagList(article_cards)
    )
  })
}

shinyApp(ui, server)