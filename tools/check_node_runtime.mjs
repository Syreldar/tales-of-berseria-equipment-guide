#!/usr/bin/env node
/**
 * Reports the Node runtime used by CI and rejects direct imports of the
 * deprecated built-in punycode module from this repository's own JavaScript.
 *
 * This probe intentionally does not inspect GitHub Actions bundles: those are
 * downloaded and executed by the runner outside the repository checkout.
 */

import { readdir, readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const repositoryRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const sourceRoots = [
    path.join(repositoryRoot, "site", "assets"),
    path.join(repositoryRoot, "tools"),
];
const sourceExtensions = new Set([".js", ".mjs", ".cjs"]);
const punycodeImportPattern = /(?:from\s*["'](?:node:)?punycode["']|require\(\s*["'](?:node:)?punycode["']\s*\)|import\(\s*["'](?:node:)?punycode["']\s*\))/g;

async function collectJavaScriptFiles(directory) {
    const entries = await readdir(directory, { withFileTypes: true });
    const files = [];

    for (const entry of entries) {
        const entryPath = path.join(directory, entry.name);

        if (entry.isDirectory()) {
            files.push(...await collectJavaScriptFiles(entryPath));
        } else if (entry.isFile() && sourceExtensions.has(path.extname(entry.name))) {
            files.push(entryPath);
        }
    }

    return files;
}

function formatRelative(filePath) {
    return path.relative(repositoryRoot, filePath).split(path.sep).join("/");
}

async function findPunycodeImports() {
    const matches = [];

    for (const root of sourceRoots) {
        const files = await collectJavaScriptFiles(root);

        for (const filePath of files) {
            const contents = await readFile(filePath, "utf8");
            const sourceLines = contents.split(/\r?\n/);

            for (let index = 0; index < sourceLines.length; index += 1) {
                if (punycodeImportPattern.test(sourceLines[index])) {
                    matches.push(`${formatRelative(filePath)}:${index + 1}: ${sourceLines[index].trim()}`);
                }

                punycodeImportPattern.lastIndex = 0;
            }
        }
    }

    return matches;
}

const directImports = await findPunycodeImports();

console.log(`Node executable: ${process.execPath}`);
console.log(`Node version: ${process.version}`);
console.log(`NODE_OPTIONS: ${process.env.NODE_OPTIONS || "(not set)"}`);
console.log(`Repository JavaScript files inspected: ${sourceRoots.map(formatRelative).join(", ")}`);

if (directImports.length > 0) {
    console.error("\nDirect deprecated punycode import(s) found in repository code:");
    directImports.forEach((match) => console.error(`- ${match}`));
    process.exitCode = 1;
} else {
    console.log("Direct deprecated punycode imports in repository code: none");
    console.log("If GitHub Actions still reports DEP0040, run the manual Node warning diagnostic workflow to capture the external action stack trace.");
}
