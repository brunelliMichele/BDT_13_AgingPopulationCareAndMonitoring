// utils.js

// This module provides utility functions used across the application.

// Calculates the age of a patient based on their birthdate string.
// Returns "N/A" if no valid birthdate is provided.
export function calculateAge(birthdateStr) {
    if (!birthdateStr) return "N/A";
    const birthdate = new Date(birthdateStr);
    const today = new Date();
    let age = today.getFullYear() - birthdate.getFullYear();
    const m = today.getMonth() - birthdate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthdate.getDate())) {
        age--;
    }
    return age;
}