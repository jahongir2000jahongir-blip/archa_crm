<template>
  <svg
    width="16"
    height="16"
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Bars -->
    <rect x="1" y="11" width="3" height="4" rx="0.5" fill="currentColor" opacity="0.35" />
    <rect x="5.5" y="8" width="3" height="7" rx="0.5" fill="currentColor" opacity="0.65" />
    <rect x="10" y="5" width="3" height="10" rx="0.5" fill="currentColor" />
    <!-- Trend line (above bar tops with ~3 gap) -->
    <path
      d="M2.5 7.5 L12.5 1.5"
      stroke="currentColor"
      stroke-width="1.4"
      stroke-linecap="round"
    />
    <!-- Arrow head -->
    <path
      d="M10.5 0.5 L12.5 1.5 L11.5 3.5"
      stroke="currentColor"
      stroke-width="1.4"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>
