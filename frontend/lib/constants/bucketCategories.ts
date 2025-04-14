export interface BucketCategory {
  value: string;
  label: string;
  color: string;
  bgColor: string;
  textColor: string;
  borderColor: string;
  darkBgColor: string; 
  darkTextColor: string;
  darkBorderColor: string;
}

export const BUCKET_CATEGORIES: BucketCategory[] = [
  {
    value: "need",
    label: "Need",
    color: "blue-700",
    bgColor: "bg-blue-200",
    textColor: "text-blue-800",
    borderColor: "border-blue-200",
    darkBgColor: "dark:bg-blue-800",
    darkTextColor: "dark:text-blue-100",
    darkBorderColor: "dark:border-blue-700"
  },
  {
    value: "want",
    label: "Want",
    color: "yellow-700",
    bgColor: "bg-yellow-200",
    textColor: "text-yellow-800",
    borderColor: "border-yellow-200", 
    darkBgColor: "dark:bg-yellow-800",
    darkTextColor: "dark:text-yellow-100",
    darkBorderColor: "dark:border-yellow-700"
  },
  {
    value: "savings/investing",
    label: "Savings/Investing",
    color: "green-700",
    bgColor: "bg-green-200",
    textColor: "text-green-800",
    borderColor: "border-green-200",
    darkBgColor: "dark:bg-green-800",
    darkTextColor: "dark:text-green-100", 
    darkBorderColor: "dark:border-green-700"
  },
  {
    value: "other",
    label: "Other",
    color: "gray-700",
    bgColor: "bg-gray-200",
    textColor: "text-gray-800",
    borderColor: "border-gray-200", 
    darkBgColor: "dark:bg-gray-800",
    darkTextColor: "dark:text-gray-100",
    darkBorderColor: "dark:border-gray-700"
  },
];

export const getCategoryByValue = (value: string): BucketCategory => {
  return BUCKET_CATEGORIES.find(cat => cat.value === value) || BUCKET_CATEGORIES[3]; // Default to "other" category
};

export const getCategoryStyles = (category: string) => {
  const categoryData = getCategoryByValue(category);
  return {
    bgColor: categoryData.bgColor,
    textColor: categoryData.textColor,
    borderColor: categoryData.borderColor,
    darkBgColor: categoryData.darkBgColor,
    darkTextColor: categoryData.darkTextColor,
    darkBorderColor: categoryData.darkBorderColor
  };
};