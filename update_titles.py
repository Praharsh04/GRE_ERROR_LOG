import json

# Define titles for each topic range based on Greenlight Test Prep curriculum
topic_titles = {
    "Quantitative Comparison Strategies": [
        "QC Question Format",
        "QC Strategy: Approximation",
        "QC Strategy: Matching Operations",
        "QC Strategy: Plugging in Numbers",
        "QC Strategy: Looking for Equality",
        "QC Strategy: Number Sense",
        "QC Strategy: Miscellaneous Tips"
    ],
    "Arithmetic": [
        "Types of Numbers",
        "Order of Operations (PEMDAS)",
        "Absolute Value Properties",
        "Fractions: Basic Operations",
        "Fractions: Comparison Techniques",
        "Decimals and Place Value",
        "Decimals: Operations",
        "Percents: Conversion Basics",
        "Percents: The Percent Equation",
        "Percent Change Formula",
        "Percent Increase/Decrease",
        "Successive Percent Changes",
        "Simple and Compound Interest",
        "Ratios: Part-to-Part",
        "Ratios: Part-to-Whole",
        "Ratios: Part-to-Whole Conversion",
        "Ratios: Scaling and Combining",
        "Proportions and Cross-Multiplication",
        "Average (Arithmetic Mean)",
        "Median: Finding the Middle Value",
        "Mode: Most Frequent Value",
        "Weighted Averages",
        "Average Speed Formula"
    ],
    "Powers and Roots": [
        "Exponents: Product Rule",
        "Exponents: Quotient Rule",
        "Exponents: Power of a Power",
        "Exponents: Power of a Product",
        "Negative Exponents Rule",
        "Zero Exponent Rule",
        "Fractional Exponents",
        "Square Roots: Basic Rules",
        "Square Roots: Simplifying Radicals",
        "Radicals: Product Rule",
        "Radicals: Quotient Rule",
        "Adding and Subtracting Radicals",
        "Roots of Negative Numbers",
        "Estimating Square Roots",
        "Square Roots of Fractions",
        "Common Perfect Squares"
    ],
    "Algebra and Equation-Solving": [
        "Simplifying Algebraic Expressions",
        "Factoring: Common Factors",
        "Factoring: FOIL Method",
        "Factoring: Difference of Squares",
        "Factoring: Quadratic Trinomials",
        "Solving Linear Equations",
        "Solving Linear Equations (v2)",
        "Equations with Two Variables",
        "Systems of Equations: Substitution",
        "Systems of Equations: Elimination",
        "Solving Quadratic Equations",
        "The Quadratic Formula",
        "Quadratic Equation: Number of Solutions",
        "Algebraic Identities",
        "Inequalities: Basic Properties",
        "Inequalities: Multiplying by Negatives",
        "Compound Inequalities",
        "Absolute Value Equations",
        "Absolute Value Inequalities",
        "Functions: Domain and Range",
        "Functions: Nested Functions",
        "Functions: Graphs",
        "Algebra: Word Translation",
        "Variable in Answer Choices",
        "Algebra: Substitution Strategy",
        "Algebra: Number Sense Strategy",
        "Algebra: Common Errors",
        "Algebra: Advanced Factoring",
        "Algebra: Algebraic Fractions",
        "Algebra: Ratio Equations",
        "Algebra: Proportionality",
        "Algebra: Direct Variation",
        "Algebra: Inverse Variation",
        "Algebra: Sequence Intro",
        "Algebra: Recursive Sequences",
        "Algebra: Patterns",
        "Algebra: Equation Tips"
    ],
    "Word Problems": [
        "Word Problems: General Strategy",
        "Distance, Rate, and Time (D=RT)",
        "Average Speed in Word Problems",
        "Work, Rate, and Time (W=RT)",
        "Work: Combined Rates Formula",
        "Work: Opposing Rates",
        "Mixture Problems: Solution Strength",
        "Mixture Problems: Weighted Averages",
        "Sets: Two-Circle Venn Diagrams",
        "Sets: Three-Circle Venn Diagrams",
        "Sets: Double Matrix Method",
        "Consecutive Integers Problems",
        "Age Word Problems",
        "Word Problems: Number Logic",
        "Word Problems: Cost and Profit",
        "Word Problems: Unit Conversion",
        "Word Problems: Rates (v2)",
        "Word Problems: Rates (v3)",
        "Word Problems: Ratios (v2)",
        "Word Problems: Geometry Integration"
    ],
    "Geometry": [
        "Lines: Intersecting and Parallel",
        "Angles: Supplementary and Vertical",
        "Triangles: Area and Perimeter",
        "Triangles: Third Side Inequality",
        "Triangles: Angle-Side Relationships",
        "Triangles: Isosceles and Equilateral",
        "Right Triangles: Pythagorean Theorem",
        "Right Triangles: 3-4-5 and 5-12-13",
        "Special Right Triangles: 45-45-90",
        "Special Right Triangles: 30-60-90",
        "Similar Triangles and Proportions",
        "Quadrilaterals: Sum of Angles",
        "Quadrilaterals: Parallelograms",
        "Quadrilaterals: Rectangles and Rhombuses",
        "Quadrilaterals: Trapezoids",
        "Polygons: Sum of Interior Angles",
        "Polygons: Regular Polygons",
        "Circles: Circumference and Radius",
        "Circles: Area Formula",
        "Circles: Arc Length and Sectors",
        "Circles: Chords and Tangents",
        "3D Figures: Rectangular Solids",
        "3D Figures: Cylinders"
    ],
    "Integer Properties": [
        "Divisibility Rules for 2, 3, 5, 10",
        "Divisibility Rules for 4, 6, 9",
        "Primes: Definition and Properties",
        "Prime Factorization",
        "Factors and Multiples",
        "Finding Number of Factors",
        "Greatest Common Factor (GCF)",
        "Least Common Multiple (LCM)",
        "GCF and LCM Relationship",
        "Remainders: Basic Definition",
        "Remainders: Pattern Recognition",
        "Even and Odd Rules",
        "Positive and Negative Rules",
        "Integers: Common Patterns",
        "Integers: Factorization (v2)"
    ],
    "Statistics": [
        "Measures of Central Tendency",
        "Standard Deviation: Definition",
        "Standard Deviation: Properties",
        "Range and Interquartile Range",
        "Normal Distribution: 68-95-99 Rule",
        "Normal Distribution: Symmetry",
        "Statistics: Quartiles and Percentiles"
    ],
    "Counting": [
        "Fundamental Counting Principle",
        "Counting: Permutations",
        "Counting: Combinations",
        "Permutations vs. Combinations",
        "Counting: Circular Arrangements",
        "Counting: Duplicate Items",
        "Counting: Restriction Problems",
        "Counting: Glue Method",
        "Counting: Separator Method"
    ],
    "Probability": [
        "Probability: Basic Definition",
        "Probability: The Complement Rule",
        "Probability: 'OR' Rule (Disjoint)",
        "Probability: 'OR' Rule (Overlapping)",
        "Probability: 'AND' Rule (Independent)",
        "Probability: 'AND' Rule (Dependent)",
        "Probability: Binomial Distribution",
        "Probability: Selection Problems",
        "Probability: Geometry Integration",
        "Probability: Expected Value"
    ],
    "Data Interpretation": [
        "Data: Reading Bar Graphs",
        "Data: Reading Line Graphs",
        "Data: Pie Charts and Circle Graphs",
        "Data: Scatter Plots and Trends"
    ]
}

def update_flashcards():
    with open('flashcards.json', 'r') as f:
        flashcards = json.load(f)
    
    # Counter for each topic
    topic_counters = {topic: 0 for topic in topic_titles}
    
    for card in flashcards:
        topic = card['topic']
        if topic in topic_titles:
            titles = topic_titles[topic]
            idx = topic_counters[topic]
            if idx < len(titles):
                card['title'] = titles[idx]
            else:
                # Fallback to topic + keyword from text
                text_snippet = card['text'].replace(topic, "").replace("Flashcards", "").strip()
                words = [w for w in text_snippet.split() if len(w) > 3][:3]
                if words:
                    card['title'] = f"{topic}: {' '.join(words)}"
                else:
                    card['title'] = f"{topic} Concept"
            topic_counters[topic] += 1
        else:
            card['title'] = "GRE Quant Concept"

    with open('flashcards.json', 'w') as f:
        json.dump(flashcards, f, indent=2)
    
    print("Updated titles for 171 flashcards.")

if __name__ == "__main__":
    update_flashcards()
