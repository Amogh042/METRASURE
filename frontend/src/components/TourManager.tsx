"use client";

import { useEffect } from "react";
import { driver } from "driver.js";
import "driver.js/dist/driver.css";

export default function TourManager() {
    useEffect(() => {
        // Initialize Driver.js
        const driverObj = driver({
            showProgress: true,
            animate: true,
            overlayOpacity: 0.65,
            allowClose: true,
            doneBtnText: 'Finish',
            nextBtnText: 'Next',
            prevBtnText: 'Back',
            steps: [
                {
                    element: '[data-tour="dashboard"]',
                    popover: {
                        title: 'Welcome to MetraSure',
                        description: 'MetraSure helps laboratories manage NAWI testing, automate calculations, and generate structured test reports.',
                        side: "bottom",
                        align: "start"
                    }
                },
                {
                    element: '[data-tour="dashboard-stats"]',
                    popover: {
                        title: 'Your Laboratory Dashboard',
                        description: 'Monitor registered instruments, completed tests, PASS/FAIL results, and generated reports from one place.',
                        side: "bottom",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="instrument-registry"]',
                    popover: {
                        title: 'Register Instruments',
                        description: 'Add and manage non-automatic weighing instruments, including manufacturer, model, serial number, accuracy class, Max, Min and verification interval.',
                        side: "bottom",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="start-test"]',
                    popover: {
                        title: 'Start an OIML Test',
                        description: 'Select an instrument and begin a guided testing workflow. Enter measurements and let the deterministic rule engine perform the calculations.',
                        side: "left",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="test-results"]',
                    popover: {
                        title: 'Review Test Results',
                        description: 'Review measurements, calculated errors, applicable limits, and transparent PASS/FAIL results.',
                        side: "top",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="reports"]',
                    popover: {
                        title: 'Generate Test Reports',
                        description: 'Generate a professional PDF test report containing the instrument details, measurements, calculations, results and applicable rule information.',
                        side: "left",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="verification"]',
                    popover: {
                        title: 'Verify Reports',
                        description: 'Each generated report can have a unique verification link and QR code so its recorded result can be checked digitally.',
                        side: "left",
                        align: "center"
                    }
                },
                {
                    element: '[data-tour="dashboard"]',
                    popover: {
                        title: "You're Ready!",
                        description: "You now know the main MetraSure workflow. You can replay this tour anytime from the Help button.",
                        side: "bottom",
                        align: "start"
                    }
                }
            ],
            onDestroyStarted: () => {
                if (!driverObj.hasNextStep() || confirm("Are you sure you want to skip the tour?")) {
                    driverObj.destroy();
                }
            },
        });

        const startTour = () => {
            // Because the layout header might take a second or be obscured on mobile, ensure smooth scrolling is active.
            driverObj.drive();
            localStorage.setItem("metrasure_tour_completed", "true");
        };

        // Check if first time user
        const hasCompletedTour = localStorage.getItem("metrasure_tour_completed");
        if (!hasCompletedTour) {
            // Small delay to ensure all DOM elements are mounted and parsed
            setTimeout(() => {
                startTour();
            }, 500);
        }

        // Attach listener to Help Button in the Layout Nav
        const helpBtn = document.getElementById("tour-help-btn");
        const handleHelpClick = () => {
            // Reset to step 0
            startTour();
        };

        if (helpBtn) {
            helpBtn.addEventListener("click", handleHelpClick);
        }

        return () => {
            if (helpBtn) {
                helpBtn.removeEventListener("click", handleHelpClick);
            }
            driverObj.destroy();
        };
    }, []);

    return null; // This is purely a logic/effect component
}
