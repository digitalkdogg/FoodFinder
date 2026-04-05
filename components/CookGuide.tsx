"use client";

import { useState } from "react";

interface RecipeInstruction {
  step_number: number;
  instruction_text: string;
}

interface CookGuideProps {
  rawIngredients: string | null;
  steps: RecipeInstruction[];
}

export default function CookGuide({ rawIngredients, steps }: CookGuideProps) {
  const [checkedSteps, setCheckedSteps] = useState<Set<number>>(new Set());

  const toggleStep = (stepNumber: number) => {
    setCheckedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(stepNumber)) {
        next.delete(stepNumber);
      } else {
        next.add(stepNumber);
      }
      return next;
    });
  };

  const ingredientLines = rawIngredients
    ? rawIngredients.split("\n").filter((line) => line.trim())
    : [];

  const completedSteps = checkedSteps.size;
  const totalSteps = steps.length;
  const progressPercent =
    totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-8 mt-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">
          👨‍🍳 Cook Guide
        </h2>
        {totalSteps > 0 && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-600">
                Progress: {completedSteps} of {totalSteps} steps
              </span>
              <span className="font-semibold text-slate-900">{progressPercent}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Left: Ingredients */}
        <div>
          <h3 className="text-xl font-semibold text-slate-900 mb-4">
            📋 What You'll Need
          </h3>
          {ingredientLines.length > 0 ? (
            <ul className="space-y-2">
              {ingredientLines.map((ingredient, idx) => (
                <li
                  key={idx}
                  className="text-slate-700 flex items-start gap-3 text-sm leading-relaxed"
                >
                  <span className="text-blue-500 font-bold mt-0.5">•</span>
                  <span>{ingredient}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 text-sm">No ingredients listed.</p>
          )}
        </div>

        {/* Right: Steps */}
        <div>
          <h3 className="text-xl font-semibold text-slate-900 mb-4">
            🎯 Steps
          </h3>
          {steps.length > 0 ? (
            <ul className="space-y-4">
              {steps.map((step) => (
                <li
                  key={step.step_number}
                  className={`flex items-start gap-3 pb-4 border-b border-slate-200 last:border-b-0 ${
                    checkedSteps.has(step.step_number) ? "opacity-60" : ""
                  }`}
                >
                  <input
                    type="checkbox"
                    id={`step-${step.step_number}`}
                    checked={checkedSteps.has(step.step_number)}
                    onChange={() => toggleStep(step.step_number)}
                    className="mt-1 w-5 h-5 cursor-pointer accent-blue-500"
                  />
                  <label
                    htmlFor={`step-${step.step_number}`}
                    className={`cursor-pointer flex-1 ${
                      checkedSteps.has(step.step_number)
                        ? "line-through text-slate-400"
                        : "text-slate-700"
                    }`}
                  >
                    <span className="font-semibold block text-sm mb-1">
                      Step {step.step_number}
                    </span>
                    <span className="text-sm leading-relaxed">
                      {step.instruction_text}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-slate-500 text-sm">No steps available.</p>
          )}
        </div>
      </div>
    </div>
  );
}
