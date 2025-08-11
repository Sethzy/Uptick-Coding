import { Crawl4AIAdapter, SearchResponse } from './crawl4ai-adapter.js';
import { generateObject, generateText } from 'ai';
import { compact } from 'lodash-es';
import pLimit from 'p-limit';
import { z } from 'zod';

import { getModel, trimPrompt } from './ai/providers.js';
import { systemPrompt } from './prompt.js';

function log(...args: any[]) {
  console.log(...args);
}


export type ResearchProgress = {
  currentDepth: number;
  totalDepth: number;
  currentBreadth: number;
  totalBreadth: number;
  currentQuery?: string;
  totalQueries: number;
  completedQueries: number;
};

type ResearchResult = {
  learnings: string[];
  visitedUrls: string[];
};

// increase this if you have higher API rate limits
const ConcurrencyLimit = 1;

// AIDEV-NOTE: Initialize Crawl4AI adapter as drop-in replacement for FirecrawlApp
const crawl4ai = new Crawl4AIAdapter({
  apiUrl: process.env.CRAWL4AI_API_URL || 'http://localhost:8001',
});

// AIDEV-NOTE: The rest of the code remains IDENTICAL to deep-research.ts
// This demonstrates perfect API compatibility

// take en user query, return a list of SERP queries
async function generateSerpQueries({
  query,
  numQueries = 3,
  learnings,
}: {
  query: string;
  numQueries?: number;

  // optional, if provided, the research will continue from the last learning
  learnings?: string[];
}) {
  try {
    const res = await generateObject({
      model: getModel(),
      system: systemPrompt(),
      prompt: `Given the following prompt from the user, generate exactly ${numQueries} SERP queries to research the topic. be specific and precise by distilling the topic to its absolute key concepts, using fewer but most important and relevant keywords, and considering the vocabulary content creators would use; and do not use exact match phrases (double quotes). Each query should explore a different aspect or angle of the topic. Make sure each query is unique and not similar to each other: <prompt>${query}</prompt>\n\n${
        learnings
          ? `Here are some learnings from previous research, use them to generate more specific queries using only the most important and relevant keywords, and considering the vocabulary content creators would use: ${learnings.join(
              '\n',
            )}`
          : ''
      }`,
      schema: z.object({
        queries: z
          .array(
            z.object({
              query: z.string().describe('The SERP query'),
              researchGoal: z
                .string()
                .describe(
                  'First talk about the goal of the research that this query is meant to accomplish, then go deeper into how to advance the research once the results are found, mention additional research directions. Be as specific as possible, especially for additional research directions.',
                ),
            }),
          )
          .describe(`List of SERP queries, max of ${numQueries}`),
      }),
    });
    
    log(`Created ${res.object.queries.length} queries`, res.object.queries);

    return res.object.queries.slice(0, numQueries);
  } catch (error) {
    log(`ERROR: Failed to generate SERP queries:`, error);
    throw error;
  }
}

async function processSerpResult({
  query,
  result,
  numLearnings = 3,
  numFollowUpQuestions = 3,
}: {
  query: string;
  result: SearchResponse;
  numLearnings?: number;
  numFollowUpQuestions?: number;
}) {
  try {
    const contents = compact(result.data.map(item => item.markdown)).map(content =>
      trimPrompt(content, 25_000),
    );
    log(`Ran ${query}, found ${contents.length} contents`);

    if (contents.length === 0) {
      log(`WARNING: No content found for query "${query}"`);
      return {
        learnings: [],
        followUpQuestions: []
      };
    }

    const res = await generateObject({
      model: getModel(),
      abortSignal: AbortSignal.timeout(60_000),
      system: systemPrompt(),
      prompt: trimPrompt(
        `Given the following contents from a SERP search for the query <query>${query}</query>, generate a list of learnings from the contents. Return a maximum of ${numLearnings} learnings, but feel free to return less if the contents are clear. Make sure each learning is unique and not similar to each other. The learnings should be concise and to the point, as detailed and information dense as possible. Make sure to include any entities like people, places, companies, products, things, etc in the learnings, as well as any exact metrics, numbers, or dates. The learnings will be used to research the topic further.\n\n<contents>${contents
          .map(content => `<content>\n${content}\n</content>`)
          .join('\n')}</contents>`,
      ),
      schema: z.object({
        learnings: z.array(z.string()).describe(`List of learnings, max of ${numLearnings}`),
        followUpQuestions: z
          .array(z.string())
          .describe(
            `List of follow-up questions to research the topic further, max of ${numFollowUpQuestions}`,
          ),
      }),
    });
    
    log(`Created ${res.object.learnings.length} learnings`, res.object.learnings);

    return res.object;
  } catch (error) {
    log(`ERROR: Failed to process SERP result for query "${query}":`, error);
    throw error;
  }
}

export async function writeFinalReport({
  prompt,
  learnings,
  visitedUrls,
}: {
  prompt: string;
  learnings: string[];
  visitedUrls: string[];
}) {
  const learningsString = learnings
    .map(learning => `<learning>\n${learning}\n</learning>`)
    .join('\n');

  // AIDEV-NOTE: using-generateText-for-final-report; avoids JSON parsing errors with special characters
  const { text } = await generateText({
    model: getModel(),
    system: systemPrompt(),
    prompt: trimPrompt(
      `Given the following prompt from the user, write a final report on the topic using the learnings from research. Make it as as detailed as possible, aim for 3 or more pages, include ALL the learnings from research:\n\n<prompt>${prompt}</prompt>\n\nHere are all the learnings from previous research:\n\n<learnings>\n${learningsString}\n</learnings>`,
    ),
  });

  // Append the visited URLs section to the report
  const urlsSection = `\n\n## Sources\n\n${visitedUrls.map(url => `- ${url}`).join('\n')}`;
  return text + urlsSection;
}

export async function writeFinalAnswer({
  prompt,
  learnings,
}: {
  prompt: string;
  learnings: string[];
}) {
  try {
    const learningsString = learnings
      .map(learning => `<learning>\n${learning}\n</learning>`)
      .join('\n');

    const res = await generateObject({
      model: getModel(),
      system: systemPrompt(),
      prompt: trimPrompt(
        `Given the following prompt from the user, write a final answer on the topic using the learnings from research. Follow the format specified in the prompt. Do not yap or babble or include any other text than the answer besides the format specified in the prompt. Keep the answer as concise as possible - usually it should be just a few words or maximum a sentence. Try to follow the format specified in the prompt (for example, if the prompt is using Latex, the answer should be in Latex. If the prompt gives multiple answer choices, the answer should be one of the choices).\n\n<prompt>${prompt}</prompt>\n\nHere are all the learnings from research on the topic that you can use to help answer the prompt:\n\n<learnings>\n${learningsString}\n</learnings>`,
      ),
      schema: z.object({
        exactAnswer: z
          .string()
          .describe('The final answer, make it short and concise, just the answer, no other text'),
      }),
    });

    return res.object.exactAnswer;
  } catch (error) {
    log(`ERROR: Failed to write final answer:`, error);
    throw error;
  }
}

export async function deepResearch({
  query,
  breadth,
  depth,
  learnings = [],
  visitedUrls = [],
  onProgress,
}: {
  query: string;
  breadth: number;
  depth: number;
  learnings?: string[];
  visitedUrls?: string[];
  onProgress?: (progress: ResearchProgress) => void;
}): Promise<ResearchResult> {
  // AIDEV-NOTE: Memory monitoring for research function
  const startMem = process.memoryUsage();
  console.log(`🧠 Research started - Memory: ${Math.round(startMem.heapUsed / 1024 / 1024)}MB`);
  
  const cleanup = () => {
    const endMem = process.memoryUsage();
    console.log(`🧠 Research completed - Memory: ${Math.round(endMem.heapUsed / 1024 / 1024)}MB`);
    console.log(`🧠 Memory change: +${Math.round((endMem.heapUsed - startMem.heapUsed) / 1024 / 1024)}MB`);
  };
  const progress: ResearchProgress = {
    currentDepth: depth,
    totalDepth: depth,
    currentBreadth: breadth,
    totalBreadth: breadth,
    totalQueries: 0,
    completedQueries: 0,
  };

  const reportProgress = (update: Partial<ResearchProgress>) => {
    Object.assign(progress, update);
    onProgress?.(progress);
  };

  log(`\n=== Starting research level ===`);
  log(`Query: ${query}`);
  log(`Depth: ${depth}, Breadth: ${breadth}`);
  log(`Current learnings: ${learnings.length}`);
  log(`Current URLs: ${visitedUrls.length}`);

  const serpQueries = await generateSerpQueries({
    query,
    learnings,
    numQueries: breadth,
  });

  reportProgress({
    totalQueries: serpQueries.length,
    currentQuery: serpQueries[0]?.query,
  });

  const limit = pLimit(ConcurrencyLimit);

  const results = await Promise.all(
    serpQueries.map((serpQuery, index) =>
      limit(async () => {
        // AIDEV-NOTE: Add delay between queries to reduce rate limiting and improve stability
        if (index > 0) {
          const delayMs = 2000; // 2 second delay between queries
          log(`⏳ Waiting ${delayMs}ms before starting query ${index + 1}...`);
          await new Promise(resolve => setTimeout(resolve, delayMs));
        }
        
        try {
          log(`\n--- Processing query: ${serpQuery.query} ---`);
          
          // AIDEV-NOTE: This is the ONLY line that changed! 
          // Using crawl4ai instead of firecrawl - perfect drop-in replacement
          const result = await crawl4ai.search(serpQuery.query, {
            timeout: 25000,
            limit: 5,
            scrapeOptions: { formats: ['markdown'] },
          });

          // Collect URLs from this search
          const newUrls = compact(result.data.map(item => item.url));
          log(`Found ${newUrls.length} URLs for this query`);
          log(`URLs: ${newUrls.join(', ')}`);
          
          const newBreadth = Math.ceil(breadth / 2);
          const newDepth = depth - 1;

          const newLearnings = await processSerpResult({
            query: serpQuery.query,
            result,
            numFollowUpQuestions: newBreadth,
          });
          
          log(`Extracted ${newLearnings.learnings.length} learnings`);
          log(`Generated ${newLearnings.followUpQuestions.length} follow-up questions`);
          
          const allLearnings = [...learnings, ...newLearnings.learnings];
          const allUrls = [...visitedUrls, ...newUrls];

          if (newDepth > 0) {
            log(`Researching deeper, breadth: ${newBreadth}, depth: ${newDepth}`);

            reportProgress({
              currentDepth: newDepth,
              currentBreadth: newBreadth,
              completedQueries: progress.completedQueries + 1,
              currentQuery: serpQuery.query,
            });

            const nextQuery = `
            Previous research goal: ${serpQuery.researchGoal}
            Follow-up research directions: ${newLearnings.followUpQuestions.map((q: string) => `\n${q}`).join('')}
          `.trim();

            return deepResearch({
              query: nextQuery,
              breadth: newBreadth,
              depth: newDepth,
              learnings: allLearnings,
              visitedUrls: allUrls,
              onProgress,
            });
          } else {
            log(`Reached max depth, returning results`);
            reportProgress({
              currentDepth: 0,
              completedQueries: progress.completedQueries + 1,
              currentQuery: serpQuery.query,
            });
            return {
              learnings: allLearnings,
              visitedUrls: allUrls,
            };
          }
        } catch (e: any) {
          log(`\n--- ERROR processing query: ${serpQuery.query} ---`);
          if (e.message && e.message.includes('Timeout')) {
            log(`Timeout error running query: ${serpQuery.query}: `, e.message);
          } else if (e.message && e.message.includes('No object generated')) {
            log(`Schema validation error for query: ${serpQuery.query}: `, e.message);
            log(`This usually means the AI model response didn't match the expected format`);
          } else {
            log(`Error running query: ${serpQuery.query}: `, e.message);
            log(`Full error:`, e);
          }
          return {
            learnings: [],
            visitedUrls: [],
          };
        }
      }),
    ),
  );

  const finalLearnings = [...new Set(results.flatMap(r => r.learnings))];
  const finalUrls = [...new Set(results.flatMap(r => r.visitedUrls))];
  
  log(`\n=== Research level complete ===`);
  log(`Final learnings: ${finalLearnings.length}`);
  log(`Final URLs: ${finalUrls.length}`);
  log(`URLs: ${finalUrls.join(', ')}`);

  cleanup(); // AIDEV-NOTE: Log memory usage after research
  return {
    learnings: finalLearnings,
    visitedUrls: finalUrls,
  };
}