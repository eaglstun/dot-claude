%% cello-style.ily — shared engraving defaults for OWNER/OPERATORS cello parts.
%% Every song's cello.ly does:  \include "cello-style.ily"
%% gen_cello.py adds the references/ dir to LilyPond's include path (-I), so the
%% bare filename resolves no matter which song directory you render from.
%%
%% This centralizes paper, staff size, and fonts the way gen_pdf.py's CSS
%% centralizes the markdown PDFs — edit here to restyle every cello part at once.

\version "2.26.0"

%% A touch larger than default so it reads from a music stand at arm's length.
#(set-global-staff-size 20)

\paper {
  #(set-paper-size "letter")
  top-margin    = 0.6\in
  bottom-margin = 0.6\in
  left-margin   = 0.7\in
  right-margin  = 0.7\in
  ragged-bottom = ##t
  print-page-number = ##t
  print-first-page-number = ##f
  %% the LilyPond ad-line at the bottom of page one — off for a clean part
  tagline = ##f
}

%% Default look for the music itself: tidy bar numbers, clear rehearsal marks.
celloLayout = \layout {
  \context {
    \Score
    %% number every system's first bar so we can talk in bar numbers like lead.md
    \override BarNumber.break-visibility = #end-of-line-invisible
    %% boxed letter rehearsal marks (A, B, C…) — inside a \context block this is a
    %% bare property assignment, not \set (which is for inside music expressions)
    markFormatter = #format-mark-box-alphabet
  }
  \context {
    \Staff
    \override VerticalAxisGroup.staff-staff-spacing.basic-distance = #12
  }
}
