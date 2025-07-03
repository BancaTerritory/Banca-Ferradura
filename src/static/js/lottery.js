document.addEventListener('DOMContentLoaded', function() {
  // Navegação entre abas
  const navItems = document.querySelectorAll('.nav-item');
  const contentSections = document.querySelectorAll('.content-section');
  
  navItems.forEach(item => {
    item.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Remover classe ativa de todos os itens
      navItems.forEach(nav => nav.classList.remove('active'));
      contentSections.forEach(section => section.classList.remove('active'));
      
      // Adicionar classe ativa ao item clicado
      this.classList.add('active');
      
      // Mostrar seção correspondente
      const targetId = this.getAttribute('data-target');
      document.getElementById(targetId).classList.add('active');
    });
  });
  
  // Controle do menu lateral
  const menuButton = document.querySelector('.balance-details');
  const closeMenuButton = document.querySelector('.close-menu');
  const sideMenu = document.querySelector('.side-menu');
  
  if (menuButton) {
    menuButton.addEventListener('click', function() {
      sideMenu.classList.add('active');
    });
  }
  
  if (closeMenuButton) {
    closeMenuButton.addEventListener('click', function() {
      sideMenu.classList.remove('active');
    });
  }
  
  // Fechar menu ao clicar fora
  document.addEventListener('click', function(e) {
    if (sideMenu.classList.contains('active') && 
        !sideMenu.contains(e.target) && 
        e.target !== menuButton) {
      sideMenu.classList.remove('active');
    }
  });
});
