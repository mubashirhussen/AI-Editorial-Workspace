import { analyzeText, countSyllables } from './textAnalysis';

// Quick deterministic test runner
function assert(condition: boolean, msg: string) {
  if (!condition) {
    throw new Error(`Assertion failed: ${msg}`);
  }
}

console.log('Testing textAnalysis utility...');

// Test 1: Empty text
const empty = analyzeText('');
assert(empty.word_count === 0, 'Empty word count must be 0');
assert(empty.sentence_count === 0, 'Empty sentence count must be 0');
assert(empty.reading_time_seconds === 0, 'Empty reading time must be 0');
assert(empty.flesch_reading_ease === 100, 'Empty flesch must be 100');

// Test 2: Basic sentence
const single = analyzeText('The quick brown fox jumps over the lazy dog.');
assert(single.word_count === 9, `Expected 9 words, got ${single.word_count}`);
assert(single.sentence_count === 1, `Expected 1 sentence, got ${single.sentence_count}`);
assert(single.reading_time_seconds >= 2 && single.reading_time_seconds <= 4, `Reading time ~3s, got ${single.reading_time_seconds}`);

// Test 3: Markdown and abbreviations
const markdownSample = `
# Editorial Review

In order to understand the significance of recent reasoning benchmarks, it is important to note that a large number of tests were conducted by the research team. e.g., the benchmark tests scored 94.2%.

## Section 2
Furthermore, this extraordinarily elongated and unnecessarily protracted sentence stretches across numerous subordinate clauses and technical parameters without giving the reader a single moment of pause or cognitive respite, which obviously makes it exceedingly difficult to parse in a fast-paced executive editorial environment. [^1]
`;

const res = analyzeText(markdownSample);
console.log('Analyzed markdown sample:', {
  words: res.word_count,
  sentences: res.sentence_count,
  reading_time_s: res.reading_time_seconds,
  flesch: res.flesch_reading_ease,
  quality_score: res.quality_score,
  long_sentences: res.complexity_issues.long_sentences,
});

assert(res.word_count > 60, 'Sample should have > 60 words');
assert(res.sentence_count >= 2, 'Sample should have >= 2 sentences');
assert(res.complexity_issues.long_sentences >= 1, 'Long sentence must be flagged');
assert(res.reading_time_seconds > 10, 'Reading time must be > 10 seconds');

// Test 4: countSyllables
assert(countSyllables('the') === 1, 'the is 1 syllable');
assert(countSyllables('protracted') === 3, 'protracted is 3 syllables');
assert(countSyllables('extraordinarily') >= 6, 'extraordinarily is >= 6 syllables');

console.log('ALL textAnalysis tests passed successfully!');

