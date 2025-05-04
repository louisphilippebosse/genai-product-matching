# genai-product-matching
GenAI Product Matching

## Compass Digital Sr. AI Engineer Take-Home Exercise Overview

Your stakeholder operates convenience-store-like markets and receives weekly shipments from suppliers, including many new products. You are provided with two CSV files: one containing the internal product list from your stakeholder, and one containing the external product list from the suppliers.

### Objective
The current process of mapping the two product lists together is slow and manual. Your goal is to explore the datasets and develop an intelligent, automated system to match external products with internal items. Ensure that your solution includes prompt engineering as part of your tech stack.

**Note:** The match has to be exact, meaning the product manufacturer, name, and size must be identical.

### Deliverables
1. **Final Result**:
   - A table including all external items with the corresponding mapped internal product. If no match is found, the table should indicate `NULL` for the internal product.
2. **Presentation**:
   - Create a 10-min presentation to demonstrate how your system works.
   - Be prepared to discuss any technical details with accompanying materials (e.g., Jupyter notebooks).

### Evaluation Criteria
- Your approach to exploring and understanding the datasets.
- The thought process behind your solution.
- The effectiveness and accuracy of your matching system.
- The clarity and accessibility of your presentation for a non-technical audience.
- Additional points for implementing a user-friendly front-end application.

### Examples
To help you understand our requirements, here are a few examples of correct and wrong matches:

#### Correct Matches:
| External_Product_Name                     | Internal_Product_Name                          |
|-------------------------------------------|-----------------------------------------------|
| DIET LIPTON GREEN TEA W/ CITRUS 20 OZ     | Lipton Diet Green Tea with Citrus (20oz)      |
| CH-CHERRY CHS CLAW DANISH 4.25 OZ         | Cloverhill Cherry Cheese Bearclaw Danish (4.25oz) |

#### Wrong Matches:
| External_Product_Name                     | Internal_Product_Name                          |
|-------------------------------------------|-----------------------------------------------|
| Cloverhill Cherry Cheese Bearclaw Danish (4.25oz) | Hersheys Almond Milk Choco 1.6 oz           |
| COOKIE PEANUT BUTTER 2OZ                  | Famous Amos Peanut Butter Cookie (2oz)        |

### Additional Information
There is no single correct approach to this task; we are interested in your problem-solving process.

Good luck!

# Step do do the project : 
create a venv.
create a service account
add the following role : 


make sure the following APIs are enabled:
```bash
gcloud services enable run.googleapis.com --project=genai-product-matching
gcloud services enable iam.googleapis.com --project=genai-product-matching
gcloud services enable aiplatform.googleapis.com --project=genai-product-matching