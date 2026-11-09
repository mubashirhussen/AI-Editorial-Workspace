/**
 * AI Editorial Workspace — Text Analysis Utility
 * 
 * Provides deterministic, real-time client-side metrics:
 * - Word Count (accounting for hyphenation, markdown, whitespace)
 * - Character Count (with and without spaces)
 * - Sentence Count (handling abbreviations, quotes, punctuation)
 * - Paragraph Count (handling double newlines)
 * - Estimated Reading Time (based on standard 200 WPM)
 * - Average Sentence Length
 * - Flesch Reading Ease Score
 * - Content Quality & Readability Score (0-100)
 */

export interface TextMetrics {
  word_count: number;
  character_count: number;
  character_count_no_spaces: number;
  sentence_count: number;
  paragraph_count: number;
  reading_time_minutes: number;
  reading_time_seconds: number;
  avg_sentence_length: number;
  flesch_reading_ease: number;
  quality_score: number;
  score_rating: 'Poor' | 'Fair' | 'Good' | 'Excellent';
  complexity_issues: {
    long_sentences: number;
    hard_words: number;
  };
}

/**
 * Counts syllables in an English word using phonetic heuristics.
 */
export function countSyllables(word: string): number {
  const cleanWord = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!cleanWord) return 0;
  if (cleanWord.length <= 3) return 1;

  // Handle -ted / -ded where 'ed' is pronounced as an extra syllable
  let working = cleanWord;
  if (/(?:[td])ed$/.test(working)) {
    // Keep the 'e' in -ted or -ded
  } else if (/ed$/.test(working)) {
    working = working.replace(/ed$/, '');
  } else {
    // Silent 'e' at end
    working = working.replace(/(?:[^laeiouy]|es|e)$/, '');
  }

  const syllableMatches = working.match(/[aeiouy]{1,2}/g);
  return syllableMatches ? Math.max(1, syllableMatches.length) : 1;
}

/**
 * Analyzes text synchronously and returns deterministic metrics.
 */
export function analyzeText(text: string): TextMetrics {
  if (!text || !text.trim()) {
    return {
      word_count: 0,
      character_count: 0,
      character_count_no_spaces: 0,
      sentence_count: 0,
      paragraph_count: 0,
      reading_time_minutes: 0,
      reading_time_seconds: 0,
      avg_sentence_length: 0,
      flesch_reading_ease: 100,
      quality_score: 100,
      score_rating: 'Excellent',
      complexity_issues: {
        long_sentences: 0,
        hard_words: 0,
      },
    };
  }

  // Strip Markdown markers for clean linguistic parsing
  const cleanText = text
    .replace(/^#+\s+/gm, '') // headings
    .replace(/[*_~`]/g, '')   // emphasis & code
    .replace(/\[\^?\d+\]/g, '') // footnote citations like [^1]
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links
    .trim();

  // Character counts
  const character_count = text.length;
  const character_count_no_spaces = text.replace(/\s/g, '').length;

  // Paragraph count
  const paragraphs = cleanText
    .split(/\n\s*\n/)
    .filter((p) => p.trim().length > 0);
  const paragraph_count = Math.max(1, paragraphs.length);

  // Word count: split on whitespace, ignore pure punctuation tokens
  const words = cleanText
    .split(/\s+/)
    .map((w) => w.replace(/^[^\w]+|[^\w]+$/g, ''))
    .filter((w) => w.length > 0);
  const word_count = words.length;

  if (word_count === 0) {
    return {
      word_count: 0,
      character_count,
      character_count_no_spaces,
      sentence_count: 0,
      paragraph_count: 0,
      reading_time_minutes: 0,
      reading_time_seconds: 0,
      avg_sentence_length: 0,
      flesch_reading_ease: 100,
      quality_score: 100,
      score_rating: 'Excellent',
      complexity_issues: {
        long_sentences: 0,
        hard_words: 0,
      },
    };
  }

  // Sentence count: split by sentence terminating punctuation (. ! ?)
  // Avoid splitting common abbreviations like e.g., i.e., vs., Dr., etc.
  const rawSentences = cleanText
    .replace(/(?:mr|mrs|ms|dr|prof|vs|inc|ltd|approx|e\.g|i\.e)\./gi, '$&_NO_BREAK_')
    .split(/(?<=[.!?])\s+(?=[A-Z0-9"'])/)
    .filter((s) => s.trim().length > 0);
  const sentence_count = Math.max(1, rawSentences.length);

  // Average Sentence Length
  const avg_sentence_length = Math.round((word_count / sentence_count) * 10) / 10;

  // Syllable calculation for Flesch Reading Ease
  let totalSyllables = 0;
  let hardWords = 0;
  for (const word of words) {
    const syl = countSyllables(word);
    totalSyllables += syl;
    if (syl >= 3) {
      hardWords++;
    }
  }

  // Count sentences with > 25 words (long/run-on sentences)
  let longSentences = 0;
  for (const s of rawSentences) {
    const sWords = s.trim().split(/\s+/).filter((w) => w.length > 0);
    if (sWords.length > 25) {
      longSentences++;
    }
  }

  // Flesch Reading Ease Formula: 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
  const asl = word_count / sentence_count;
  const asw = totalSyllables / word_count;
  let flesch = 206.835 - (1.015 * asl) - (84.6 * asw);
  flesch = Math.max(0, Math.min(100, Math.round(flesch * 10) / 10));

  // Quality score (0-100):
  // Baseline: 85
  // Deductions:
  // - each long sentence (>25 words): -4 points
  // - very high hard word ratio (>20%): -8 points
  // - extreme average sentence length (>24 words): -10 points
  // Bonuses:
  // - ideal sentence length (15-20 words): +5 points
  // - solid Flesch score (60-80): +10 points
  let score = 80;
  if (asl >= 14 && asl <= 20) score += 8;
  else if (asl > 25) score -= Math.min(20, Math.round((asl - 25) * 2));

  if (flesch >= 60 && flesch <= 80) score += 7;
  else if (flesch < 45) score -= 12;

  score -= Math.min(25, longSentences * 5);
  const hardWordRatio = hardWords / word_count;
  if (hardWordRatio > 0.25) score -= 10;

  const quality_score = Math.max(10, Math.min(100, Math.round(score)));

  let score_rating: 'Poor' | 'Fair' | 'Good' | 'Excellent' = 'Good';
  if (quality_score >= 85) score_rating = 'Excellent';
  else if (quality_score >= 70) score_rating = 'Good';
  else if (quality_score >= 50) score_rating = 'Fair';
  else score_rating = 'Poor';

  // Reading time (200 words per minute)
  const reading_time_minutes = word_count / 200;
  const reading_time_seconds = Math.max(1, Math.round((word_count / 200) * 60));

  return {
    word_count,
    character_count,
    character_count_no_spaces,
    sentence_count,
    paragraph_count,
    reading_time_minutes,
    reading_time_seconds,
    avg_sentence_length,
    flesch_reading_ease: flesch,
    quality_score,
    score_rating,
    complexity_issues: {
      long_sentences: longSentences,
      hard_words: hardWords,
    },
  };
}
