import { Component,  HostListener } from '@angular/core';

@Component({
  selector: 'app-documentation',
  templateUrl: './documentation.html',
  styleUrl: './documentation.css',
})

export class Documentation { 
    isScrolled = false;
    activeSection = 'hero';
    mobileOpen = false;

    @HostListener('window:scroll')
    onScroll(): void {
        this.isScrolled = window.scrollY > 50;
    }
        

    scrollTo(sectionId: string, event: Event): void {
        event.preventDefault();
        const el = document.getElementById(sectionId);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
        this.mobileOpen = false;
    }
}


